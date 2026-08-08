package com.travelmate.domain.expense.service;

import com.travelmate.common.enums.ExpenseCategory;
import com.travelmate.common.exception.AppException;
import com.travelmate.domain.expense.dto.*;
import com.travelmate.domain.expense.entity.Expense;
import com.travelmate.domain.expense.entity.ExpenseSplit;
import com.travelmate.domain.expense.repository.ExpenseRepository;
import com.travelmate.domain.expense.repository.ExpenseSplitRepository;
import com.travelmate.domain.trip.entity.Trip;
import com.travelmate.domain.trip.entity.TripMember;
import com.travelmate.domain.trip.repository.TripMemberRepository;
import com.travelmate.domain.trip.service.TripService;
import com.travelmate.domain.user.entity.User;
import com.travelmate.domain.user.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.*;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Transactional
public class ExpenseService {

    private final ExpenseRepository expenseRepository;
    private final ExpenseSplitRepository splitRepository;
    private final TripMemberRepository memberRepository;
    private final TripService tripService;
    private final UserRepository userRepository;

    // ─── LIST ──────────────────────────────────────────────
    @Transactional(readOnly = true)
    public List<ExpenseResponse> getExpenses(Long tripId, User user) {
        tripService.getTripAsMember(tripId, user.getId());
        return expenseRepository.findAllByTripIdOrderByExpenseDateDescCreatedAtDesc(tripId)
                .stream().map(ExpenseResponse::from).toList();
    }

    // ─── SUMMARY ───────────────────────────────────────────
    @Transactional(readOnly = true)
    public ExpenseSummaryResponse getSummary(Long tripId, User user) {
        Trip trip = tripService.getTripAsMember(tripId, user.getId());

        BigDecimal total = Optional.ofNullable(expenseRepository.sumByTripId(tripId))
                .orElse(BigDecimal.ZERO);

        Map<ExpenseCategory, BigDecimal> byCategory = new EnumMap<>(ExpenseCategory.class);
        expenseRepository.sumByCategory(tripId).forEach(row ->
                byCategory.put((ExpenseCategory) row[0], (BigDecimal) row[1]));

        Double percent = null;
        if (trip.getBudget() != null && trip.getBudget().compareTo(BigDecimal.ZERO) > 0) {
            percent = total.divide(trip.getBudget(), 4, RoundingMode.HALF_UP)
                    .multiply(BigDecimal.valueOf(100)).doubleValue();
        }

        List<ExpenseResponse> recent = expenseRepository
                .findAllByTripIdOrderByExpenseDateDescCreatedAtDesc(tripId)
                .stream().limit(5).map(ExpenseResponse::from).toList();

        return new ExpenseSummaryResponse(total, trip.getBudget(), percent, byCategory, recent);
    }

    // ─── BALANCE / SETTLEMENT ──────────────────────────────
    @Transactional(readOnly = true)
    public BalanceResponse getBalances(Long tripId, User user) {
        Trip trip = tripService.getTripAsMember(tripId, user.getId());

        BigDecimal total = Optional.ofNullable(expenseRepository.sumByTripId(tripId))
                .orElse(BigDecimal.ZERO);

        List<TripMember> members = memberRepository.findAllByTripId(tripId);
        Map<Long, BigDecimal> netBalance = new HashMap<>(); // positive = others owe this person

        for (TripMember m : members) {
            Long uid = m.getUser().getId();
            BigDecimal paid = Optional.ofNullable(splitRepository.sumPaidByUser(tripId, uid))
                    .orElse(BigDecimal.ZERO);
            BigDecimal owed = Optional.ofNullable(splitRepository.sumOwedByUser(tripId, uid))
                    .orElse(BigDecimal.ZERO);
            netBalance.put(uid, paid.subtract(owed)); // positive means others owe them
        }

        // Greedy debt simplification
        List<BalanceResponse.DebtInfo> debts = simplifyDebts(netBalance, members);

        Double percent = null;
        if (trip.getBudget() != null && trip.getBudget().compareTo(BigDecimal.ZERO) > 0) {
            percent = total.divide(trip.getBudget(), 4, RoundingMode.HALF_UP)
                    .multiply(BigDecimal.valueOf(100)).doubleValue();
        }

        return new BalanceResponse(total, trip.getBudget(), percent, debts);
    }

    private List<BalanceResponse.DebtInfo> simplifyDebts(Map<Long, BigDecimal> netBalance,
                                                           List<TripMember> members) {
        Map<Long, String> nameMap = members.stream()
                .collect(Collectors.toMap(m -> m.getUser().getId(), m -> m.getUser().getFullName()));

        // Separate creditors (positive) and debtors (negative)
        PriorityQueue<Map.Entry<Long, BigDecimal>> creditors = new PriorityQueue<>(
                Comparator.<Map.Entry<Long, BigDecimal>, BigDecimal>comparing(Map.Entry::getValue).reversed());
        PriorityQueue<Map.Entry<Long, BigDecimal>> debtors = new PriorityQueue<>(
                Comparator.comparing(Map.Entry::getValue));

        netBalance.forEach((uid, balance) -> {
            if (balance.compareTo(BigDecimal.ZERO) > 0) creditors.offer(Map.entry(uid, balance));
            else if (balance.compareTo(BigDecimal.ZERO) < 0) debtors.offer(Map.entry(uid, balance.abs()));
        });

        List<BalanceResponse.DebtInfo> result = new ArrayList<>();
        while (!creditors.isEmpty() && !debtors.isEmpty()) {
            var creditor = creditors.poll();
            var debtor = debtors.poll();
            BigDecimal settle = creditor.getValue().min(debtor.getValue());

            result.add(new BalanceResponse.DebtInfo(
                    new BalanceResponse.UserInfo(debtor.getKey(), nameMap.get(debtor.getKey())),
                    new BalanceResponse.UserInfo(creditor.getKey(), nameMap.get(creditor.getKey())),
                    settle
            ));

            BigDecimal remCreditor = creditor.getValue().subtract(settle);
            BigDecimal remDebtor = debtor.getValue().subtract(settle);
            if (remCreditor.compareTo(BigDecimal.ZERO) > 0) creditors.offer(Map.entry(creditor.getKey(), remCreditor));
            if (remDebtor.compareTo(BigDecimal.ZERO) > 0) debtors.offer(Map.entry(debtor.getKey(), remDebtor));
        }
        return result;
    }

    // ─── CREATE ────────────────────────────────────────────
    public ExpenseResponse createExpense(Long tripId, User currentUser, CreateExpenseRequest request) {
        Trip trip = tripService.getTripAsEditorOrOwner(tripId, currentUser.getId());

        User paidBy = currentUser;
        if (request.paidByUserId() != null && !request.paidByUserId().equals(currentUser.getId())) {
            paidBy = userRepository.findById(request.paidByUserId())
                    .orElseThrow(() -> AppException.notFound("User"));
        }

        Expense expense = Expense.builder()
                .trip(trip)
                .name(request.name())
                .amount(request.amount())
                .category(request.category())
                .expenseDate(request.expenseDate())
                .paidBy(paidBy)
                .note(request.note())
                .build();
        expenseRepository.save(expense);

        // Build splits
        List<ExpenseSplit> splits = buildSplits(expense, request, currentUser);
        expense.getSplits().addAll(splits);
        expenseRepository.save(expense);

        return ExpenseResponse.from(expense);
    }

    private List<ExpenseSplit> buildSplits(Expense expense, CreateExpenseRequest request, User currentUser) {
        List<ExpenseSplit> splits = new ArrayList<>();
        BigDecimal total = expense.getAmount();

        switch (request.splitType()) {
            case SINGLE -> {
                splits.add(ExpenseSplit.builder()
                        .expense(expense).user(expense.getPaidBy()).amount(total).build());
            }
            case EQUAL -> {
                List<Long> ids = request.splitWithUserIds();
                if (ids == null || ids.isEmpty()) ids = List.of(currentUser.getId());
                int count = ids.size();
                BigDecimal each = total.divide(BigDecimal.valueOf(count), 0, RoundingMode.DOWN);
                BigDecimal remainder = total.subtract(each.multiply(BigDecimal.valueOf(count)));

                for (int i = 0; i < ids.size(); i++) {
                    User u = userRepository.findById(ids.get(i))
                            .orElseThrow(() -> AppException.notFound("User"));
                    BigDecimal amt = (i == 0) ? each.add(remainder) : each; // remainder goes to payer
                    splits.add(ExpenseSplit.builder().expense(expense).user(u).amount(amt).build());
                }
            }
            case CUSTOM -> {
                if (request.customSplits() == null || request.customSplits().isEmpty()) {
                    throw AppException.badRequest("INVALID_SPLITS", "Chia tùy chỉnh cần danh sách chi tiết");
                }
                BigDecimal splitTotal = request.customSplits().values().stream()
                        .reduce(BigDecimal.ZERO, BigDecimal::add);
                if (splitTotal.compareTo(total) != 0) {
                    throw AppException.badRequest("SPLIT_MISMATCH",
                            "Tổng chia (" + splitTotal + ") không khớp số tiền (" + total + ")");
                }
                request.customSplits().forEach((uid, amt) -> {
                    User u = userRepository.findById(uid)
                            .orElseThrow(() -> AppException.notFound("User"));
                    splits.add(ExpenseSplit.builder().expense(expense).user(u).amount(amt).build());
                });
            }
        }
        return splits;
    }

    // ─── UPDATE ────────────────────────────────────────────
    public ExpenseResponse updateExpense(Long tripId, Long expenseId, User user,
                                          CreateExpenseRequest request) {
        tripService.getTripAsEditorOrOwner(tripId, user.getId());
        Expense expense = expenseRepository.findById(expenseId)
                .orElseThrow(() -> AppException.notFound("Expense"));
        if (!expense.getTrip().getId().equals(tripId)) throw AppException.notFound("Expense");

        expense.getSplits().clear();
        expense.setName(request.name());
        expense.setAmount(request.amount());
        expense.setCategory(request.category());
        expense.setExpenseDate(request.expenseDate());
        expense.setNote(request.note());
        expenseRepository.save(expense);

        List<ExpenseSplit> splits = buildSplits(expense, request, user);
        expense.getSplits().addAll(splits);
        return ExpenseResponse.from(expenseRepository.save(expense));
    }

    // ─── DELETE ────────────────────────────────────────────
    public void deleteExpense(Long tripId, Long expenseId, User user) {
        tripService.getTripAsEditorOrOwner(tripId, user.getId());
        Expense expense = expenseRepository.findById(expenseId)
                .orElseThrow(() -> AppException.notFound("Expense"));
        if (!expense.getTrip().getId().equals(tripId)) throw AppException.notFound("Expense");
        expenseRepository.delete(expense);
    }

    // ─── SETTLE ────────────────────────────────────────────
    public void settleSplit(Long tripId, Long splitId, User user) {
        tripService.getTripAsEditorOrOwner(tripId, user.getId());
        ExpenseSplit split = splitRepository.findById(splitId)
                .orElseThrow(() -> AppException.notFound("ExpenseSplit"));
        split.settle();
        splitRepository.save(split);
    }
}
