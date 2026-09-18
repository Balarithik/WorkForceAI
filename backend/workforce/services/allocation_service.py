from ortools.linear_solver import pywraplp
from workforce.models import Employee, Task, Assignment

class AllocationService:
    @staticmethod
    def optimize_allocation(tasks, candidates_matrix):
        """
        tasks: list of Task objects to assign
        candidates_matrix: dict of task_id -> list of candidate dicts
        candidate dict: {"employee": Employee, "suitability_score": float, ...}
        """
        solver = pywraplp.Solver.CreateSolver('SCIP')
        if not solver:
            return None
            
        assignments = {} # (task_id, employee_id) -> var
        objective = solver.Objective()
        
        # 1. Variables and Objective
        for task in tasks:
            candidates = candidates_matrix.get(task.id, [])
            for cand in candidates:
                emp = cand["employee"]
                score = cand["suitability_score"]
                
                # Only consider candidates above a minimum threshold if we want, but let's include all valid
                var_name = f"assign_{task.id}_{emp.id}"
                var = solver.BoolVar(var_name)
                assignments[(task.id, emp.id)] = var
                
                # Maximize suitability score
                objective.SetCoefficient(var, score)
                
        objective.SetMaximization()
        
        # 2. Constraints
        
        # C1: Each task must be assigned to exactly one employee
        for task in tasks:
            task_vars = []
            candidates = candidates_matrix.get(task.id, [])
            for cand in candidates:
                emp = cand["employee"]
                if (task.id, emp.id) in assignments:
                    task_vars.append(assignments[(task.id, emp.id)])
                    
            if task_vars:
                solver.Add(sum(task_vars) == 1)
        
        # C2: Employees workload capacity constraint
        all_employees = set()
        for task in tasks:
            for cand in candidates_matrix.get(task.id, []):
                all_employees.add(cand["employee"])
                
        for emp in all_employees:
            emp_vars = []
            for task in tasks:
                if (task.id, emp.id) in assignments:
                    # Coefficient = estimated_effort_hours
                    emp_vars.append(assignments[(task.id, emp.id)] * task.estimated_effort_hours)
            
            # Simplified workload limit constraint: Don't let estimated effort exceed remaining workload percent hours
            # Assuming 100% workload = 40 hours for simplicity, so remaining capacity in hours
            capacity_hours = max((100 - emp.current_workload_percent) / 100.0 * 40, 0)
            if emp_vars:
                solver.Add(sum(emp_vars) <= capacity_hours)
                
        # 3. Solve
        status = solver.Solve()
        
        if status == pywraplp.Solver.OPTIMAL or status == pywraplp.Solver.FEASIBLE:
            results = []
            for task in tasks:
                candidates = candidates_matrix.get(task.id, [])
                for cand in candidates:
                    emp = cand["employee"]
                    if (task.id, emp.id) in assignments and assignments[(task.id, emp.id)].solution_value() > 0.5:
                        results.append({
                            "task": task,
                            "employee": emp,
                            "metrics": cand
                        })
            return results
        
        return None
