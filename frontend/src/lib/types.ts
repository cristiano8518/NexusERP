export type AuditLog = {
  id: number;
  actor_name: string | null;
  action: string;
  resource_type: string;
  resource_id: string;
  message: string;
  changes: Record<string, unknown>;
  ip_address: string | null;
  created_at: string;
};

export type TaskAttachment = {
  id: number;
  file: string;
  file_url: string | null;
  original_name: string;
  size: number;
  uploaded_by: number | null;
  uploaded_by_name: string | null;
  created_at: string;
};

export type PerformanceStats = {
  departments: Array<{
    id: number;
    name: string;
    employee_count: number;
    manager_name: string | null;
    tasks_total: number;
    tasks_completed: number;
    tasks_overdue: number;
    completion_rate: number;
  }>;
  managers: Array<{
    id: number;
    name: string;
    department: string;
    team_size: number;
    tasks_total: number;
    tasks_completed: number;
    completion_rate: number;
  }>;
  employees: Array<{
    id: number;
    name: string;
    department: string;
    active_tasks: number;
    tasks_total: number;
    tasks_completed: number;
    tasks_overdue: number;
    completion_rate: number;
    workload: string;
  }>;
};

export type NotificationPreference = {
  email_enabled: boolean;
  in_app_enabled: boolean;
  muted_types: string[];
  updated_at: string;
};

export type PaginatedResponse<T> = {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
};

export type Employee = {
  id: number;
  employee_id: string;
  department: number;
  department_name: string;
  position: number;
  position_title: string;
  salary: string | null;
  manager: number | null;
  manager_name: string | null;
  is_active: boolean;
  is_blocked?: boolean;
  hire_date: string;
  created_at: string;
  user: {
    username: string;
    first_name: string;
    last_name: string;
    email: string;
    role: "admin" | "manager" | "employee";
  };
};

export type EmployeeDetail = Employee & {
  task_summary: {
    total: number;
    assigned: number;
    in_progress: number;
    done: number;
    approved: number;
    completion_rate: number;
    overdue?: number;
  };
  workload?: {
    active_tasks: number;
    status: string;
  };
  recent_tasks: Array<{
    id: number;
    title: string;
    status: string;
    status_display: string;
    priority: string;
    deadline: string | null;
    progress: number;
  }>;
};

export type Task = {
  id: number;
  title: string;
  description: string;
  status: string;
  status_display: string;
  priority: string;
  priority_display: string;
  assignee: number | null;
  assignee_name: string | null;
  deadline: string | null;
  progress: number;
  started_at: string | null;
  submitted_at: string | null;
  completed_at: string | null;
  approved_at: string | null;
  rejected_at: string | null;
  approval_note: string;
  is_overdue: boolean;
  created_at: string;
  updated_at: string;
};

export type TaskComment = {
  id: number;
  author: number | null;
  author_name: string | null;
  message: string;
  created_at: string;
};

export type TaskActivity = {
  id: number;
  actor: number | null;
  actor_name: string | null;
  action: string;
  action_display: string;
  from_status: string;
  to_status: string;
  message: string;
  created_at: string;
};

export type TaskDetail = Task & {
  comments: TaskComment[];
  activities: TaskActivity[];
  attachments?: TaskAttachment[];
};

export type Product = {
  id: number;
  sku: string;
  name: string;
  category: number;
  category_name: string;
  quantity: string;
  min_stock_level: string;
  is_low_stock: boolean;
  price: string;
  inventory_value: string;
};

export type FinanceEntry = {
  id: number;
  entry_type: "income" | "expense";
  title: string;
  amount: string;
  category: string;
  description: string;
  entry_date: string;
  created_by: number | null;
  created_by_name: string | null;
  created_at: string;
};

export type Department = {
  id: number;
  name: string;
  description: string;
  manager: number | null;
  manager_id: number | null;
  manager_name: string | null;
  is_active: boolean;
  employees_count: number;
  positions_count: number;
};

export type Position = {
  id: number;
  title: string;
  department: number;
  department_name: string;
  base_salary: string;
  employees_count: number;
  is_active: boolean;
};

export type Category = {
  id: number;
  name: string;
};

export type StockMovement = {
  id: number;
  product: number;
  product_name: string;
  movement_type: "in" | "out";
  quantity: string;
  unit_price: string;
  total_amount: string;
  note: string;
  auto_create_finance: boolean;
  finance_entry_id: number | null;
  created_at: string;
};

export type MonthlyFinance = {
  month: string;
  income: number;
  expense: number;
};

export type SecurityLog = {
  id: number;
  username: string | null;
  event_type: string;
  ip_address: string | null;
  created_at: string;
};

export type NotificationItem = {
  id: number;
  actor: number | null;
  actor_name: string | null;
  notification_type: string;
  type_display: string;
  priority: "low" | "normal" | "high";
  title: string;
  message: string;
  link: string;
  metadata: Record<string, unknown>;
  is_read: boolean;
  read_at: string | null;
  created_at: string;
};
