AI-04 Local Model Testing

1. Put these files in one folder:
   task_success_model.pkl
   sla_model.pkl
   completion_time_model.pkl
   test_models.py
   rank_employees.py

2. Create a virtual environment:
   python -m venv .venv

3. Activate it.

   Windows:
      .venv\Scripts\activate

   macOS/Linux:
      source .venv/bin/activate

4. Install dependencies:
   pip install -r requirements.txt

5. Test one employee + one task:
   python test_models.py

6. Test ranking multiple employees:
   python rank_employees.py

IMPORTANT:
These pickle files were trained with scikit-learn 1.6.1.
Use the pinned version above for reliable loading.

Only load pickle/joblib files that you trust, because deserializing
pickle-based model files can execute code.
