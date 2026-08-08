package com.travelmate.domain.expense.repository;

import com.travelmate.domain.expense.entity.ExpenseSplit;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.math.BigDecimal;
import java.util.List;

public interface ExpenseSplitRepository extends JpaRepository<ExpenseSplit, Long> {

    List<ExpenseSplit> findAllByExpenseId(Long expenseId);

    @Query("""  
            SELECT es FROM ExpenseSplit es
            JOIN es.expense e
            WHERE e.trip.id = :tripId
            AND es.user.id = :userId
            AND es.isSettled = false
            """)
    List<ExpenseSplit> findUnsettledByTripAndUser(@Param("tripId") Long tripId,
                                                   @Param("userId") Long userId);

    @Query("SELECT SUM(es.amount) FROM ExpenseSplit es JOIN es.expense e WHERE e.trip.id = :tripId AND es.user.id = :userId")
    BigDecimal sumOwedByUser(@Param("tripId") Long tripId, @Param("userId") Long userId);

    @Query("SELECT SUM(e.amount) FROM Expense e WHERE e.trip.id = :tripId AND e.paidBy.id = :userId")
    BigDecimal sumPaidByUser(@Param("tripId") Long tripId, @Param("userId") Long userId);
}
