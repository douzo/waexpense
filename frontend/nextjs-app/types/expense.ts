export interface Expense {
  id: string;
  merchant: string;
  amount: number;
  currency: string;
  category: string;
  expense_date: string;
  notes?: string | null;
}
