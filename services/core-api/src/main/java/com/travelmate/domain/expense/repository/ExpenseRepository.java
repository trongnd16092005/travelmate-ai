package com.travelmate.domain.expense.repository;

import com.travelmate.common.enums.ExpenseCategory;
import com.travelmate.domain.expense.entity.Expense;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.math.BigDecimal;
import java.util.List;

public interface ExpenseRepository extends JpaRepository<Expense, Long> {

    List<Expense> findAllByTripIdOrderByExpenseDateDescCreatedAtDesc(Long tripId);

    @Query("SELECT SUM(e.amount) FROM Expense e WHERE e.trip.id = :tripId")
    BigDecimal sumByTripId(@Param("tripId") Long tripId);

    @Query("SELECT e.category, SUM(e.amount) FROM Expense e WHERE e.trip.id = :tripId GROUP BY e.category")
    List<Object[]> sumByCategory(@Param("tripId") Long tripId);

    @Query("SELECT e FROM Expense e JOIN FETCH e.splits WHERE e.trip.id = :tripId")
    List<Expense> findAllWithSplitsByTripId(@Param("tripId") Long tripId);
}
