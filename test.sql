SELECT
  DAY,
  GROUP_CONCAT(total_amount || ' ' || symbol, ', ') AS total
FROM
  (
    SELECT
      e.day,
      symbol,
      SUM(e.amount) total_amount
    FROM
      expense_expense e
      INNER JOIN expense_currency c ON c.id = e.currency_id
    WHERE
      user_id = 2
    GROUP BY
      e.day,
      currency_id
    ORDER BY
      DAY ASC,
      total_amount DESC
  )
GROUP BY
  DAY