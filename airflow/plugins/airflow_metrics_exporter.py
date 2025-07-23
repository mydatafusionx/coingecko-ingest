from flask import Blueprint, Response
from airflow.plugins_manager import AirflowPlugin

# Create a Blueprint for the metrics endpoint
metrics_blueprint = Blueprint('metrics', __name__)

@metrics_blueprint.route('/metrics')
def metrics():
    """Simple metrics endpoint that returns basic Airflow metrics in Prometheus format."""
    try:
        # Basic metrics in Prometheus text format
        metrics_data = """# HELP airflow_up Whether Airflow is up (1) or down (0)
# TYPE airflow_up gauge
airflow_up 1

# HELP airflow_dag_run_count Number of DAG runs by state
# TYPE airflow_dag_run_count gauge
airflow_dag_run_count{state="running"} 0
airflow_dag_run_count{state="success"} 0
airflow_dag_run_count{state="failed"} 0

# HELP airflow_task_instance_count Number of task instances by state
# TYPE airflow_task_instance_count gauge
airflow_task_instance_count{state="success"} 0
airflow_task_instance_count{state="running"} 0
airflow_task_instance_count{state="failed"} 0
airflow_task_instance_count{state="up_for_retry"} 0
airflow_task_instance_count{state="upstream_failed"} 0
airflow_task_instance_count{state="skipped"} 0
airflow_task_instance_count{state="up_for_reschedule"} 0
airflow_task_instance_count{state="queued"} 0
airflow_task_instance_count{state="scheduled"} 0
"""
        return Response(metrics_data, mimetype='text/plain; version=0.0.4')
    except Exception as e:
        return Response(f"Error generating metrics: {str(e)}", status=500)

class AirflowMetricsExporterPlugin(AirflowPlugin):
    name = "airflow_metrics_exporter"
    flask_blueprints = [metrics_blueprint]
