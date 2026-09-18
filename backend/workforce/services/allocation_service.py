import os

from workforce.models import Employee, Task, Assignment

try:
    from ortools.linear_solver import pywraplp
except Exception:
    pywraplp = None

class AllocationService:
    MIN_SKILL_MATCH = float(os.getenv('MIN_SKILL_MATCH', '0.5'))
    MAX_WORKLOAD_PERCENT = float(os.getenv('MAX_WORKLOAD_PERCENT', '100'))
    HOURS_PER_WORKDAY = float(os.getenv('HOURS_PER_WORKDAY', '40'))

    @classmethod
    def effective_workload_hours(cls, employee):
        return employee.current_workload_percent / 100.0 * cls.HOURS_PER_WORKDAY

    @staticmethod
    def optimize_allocation(tasks, candidates_matrix):
        """
        tasks: list of Task objects to assign
        candidates_matrix: dict of task_id -> list of candidate dicts
        candidate dict: {"employee": Employee, "suitability_score": float, ...}
        """
        if pywraplp is None:
            return None

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
                if emp.availability != 'AVAILABLE':
                    continue
                if cand.get('skill_match_score', 0) < AllocationService.MIN_SKILL_MATCH:
                    continue
                if cand.get('predicted_completion_hours', 0) > task.sla_hours:
                    continue
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
            
            capacity_hours = max(
                (AllocationService.MAX_WORKLOAD_PERCENT / 100.0 * AllocationService.HOURS_PER_WORKDAY)
                - AllocationService.effective_workload_hours(emp),
                0,
            )
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
