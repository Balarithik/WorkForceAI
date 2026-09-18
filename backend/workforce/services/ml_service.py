import logging
import os
import warnings

import joblib
from django.conf import settings

from .feature_service import extract_features

logger = logging.getLogger(__name__)
warnings.filterwarnings('ignore', category=UserWarning, module='xgboost')

MODEL_COLUMNS = [
    'experience_years_x',
    'skill_match_score',
    'employee_workload_percent',
    'historical_performance_score',
    'estimated_effort_hours_y',
    'sla_hours_y',
    'task_type_y',
    'task_priority_y',
    'workload_capacity',
    'sla_urgency_ratio',
    'experience_performance_score',
    'workload_effort_ratio',
]


class MLService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MLService, cls).__new__(cls)
            cls._instance._load_models()
        return cls._instance

    def _load_models(self):
        ml_dir = getattr(settings, 'ML_MODEL_DIR', os.path.join(settings.BASE_DIR, 'ml_models'))
        files = {
            'success': os.path.join(ml_dir, 'task_success_model.pkl'),
            'sla': os.path.join(ml_dir, 'sla_model.pkl'),
            'completion': os.path.join(ml_dir, 'completion_time_model.pkl'),
        }

        missing = [path for path in files.values() if not os.path.exists(path)]
        if missing:
            self.success_model = None
            self.sla_model = None
            self.completion_model = None
            self.models_loaded = False
            logger.error('ML model files missing: %s', missing)
            return

        try:
            self.success_model = joblib.load(files['success'])
            self.sla_model = joblib.load(files['sla'])
            self.completion_model = joblib.load(files['completion'])
            self.models_loaded = True
            logger.info('ML models loaded successfully from %s', ml_dir)
        except Exception:
            logger.exception('Failed to load ML models from %s', ml_dir)
            self.success_model = None
            self.sla_model = None
            self.completion_model = None
            self.models_loaded = False

    @staticmethod
    def _prepare_feature_frame(feature_rows):
        import pandas as pd

        if not feature_rows:
            return pd.DataFrame(columns=MODEL_COLUMNS)

        df = pd.DataFrame(feature_rows)
        missing = [col for col in MODEL_COLUMNS if col not in df.columns]
        if missing:
            raise ValueError(f'ML feature frame missing required columns: {missing}')

        extra = [col for col in df.columns if col not in MODEL_COLUMNS]
        if extra:
            df = df.drop(columns=extra)

        df = df.loc[:, MODEL_COLUMNS]
        for col in ['experience_years_x', 'skill_match_score', 'employee_workload_percent', 'historical_performance_score', 'estimated_effort_hours_y', 'sla_hours_y', 'workload_capacity', 'sla_urgency_ratio', 'experience_performance_score', 'workload_effort_ratio']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df['task_type_y'] = df['task_type_y'].fillna('Software Development').astype(str)
        df['task_priority_y'] = df['task_priority_y'].fillna('Medium').astype(str)
        return df

    def predict_employee_task(self, employee, task):
        if not self.models_loaded or self.success_model is None or self.sla_model is None or self.completion_model is None:
            raise RuntimeError('ML models are not loaded or are unavailable.')

        feature_row = extract_features(employee, task)
        df = self._prepare_feature_frame([feature_row])

        success_probability = float(self.success_model.predict_proba(df)[0][1])
        sla_probability = float(self.sla_model.predict_proba(df)[0][1])
        predicted_hours = float(self.completion_model.predict(df)[0])

        time_score = min(1.0, task.sla_hours / max(predicted_hours, 0.1))
        suitability_score = 100 * (
            0.50 * success_probability +
            0.30 * sla_probability +
            0.20 * time_score
        )

        return {
            'success_probability': success_probability,
            'sla_probability': sla_probability,
            'predicted_completion_hours': predicted_hours,
            'time_score': time_score,
            'score_breakdown': {
                'success_contribution': 50 * success_probability,
                'sla_contribution': 30 * sla_probability,
                'time_contribution': 20 * time_score,
            },
            'suitability_score': suitability_score,
        }

    def batch_predict(self, employees, task):
        if not self.models_loaded or self.success_model is None or self.sla_model is None or self.completion_model is None:
            raise RuntimeError('ML models are not loaded or are unavailable.')

        if not employees:
            return []

        feature_list = [extract_features(emp, task) for emp in employees]
        df = self._prepare_feature_frame(feature_list)

        success_probs = self.success_model.predict_proba(df)[:, 1]
        sla_probs = self.sla_model.predict_proba(df)[:, 1]
        completion_times = self.completion_model.predict(df)

        results = []
        for i, emp in enumerate(employees):
            success_probability = float(success_probs[i])
            sla_probability = float(sla_probs[i])
            predicted_hours = float(completion_times[i])

            time_score = min(1.0, task.sla_hours / max(predicted_hours, 0.1))
            suitability_score = 100 * (
                0.50 * success_probability +
                0.30 * sla_probability +
                0.20 * time_score
            )

            results.append({
                'employee': emp,
                'skill_match_score': feature_list[i]['skill_match_score'],
                'success_probability': success_probability,
                'sla_probability': sla_probability,
                'predicted_completion_hours': predicted_hours,
                'time_score': time_score,
                'available_capacity_percent': max(100 - emp.current_workload_percent, 0),
                'score_breakdown': {
                    'success_contribution': 50 * success_probability,
                    'sla_contribution': 30 * sla_probability,
                    'time_contribution': 20 * time_score,
                },
                'suitability_score': suitability_score,
            })

        return results


ml_service = MLService()
