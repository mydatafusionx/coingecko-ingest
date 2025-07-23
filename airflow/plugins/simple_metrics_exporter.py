from flask import Blueprint, Response
from airflow.plugins_manager import AirflowPlugin
from airflow.models import DagRun, TaskInstance
from airflow.utils.session import provide_session
from sqlalchemy import func

# Create a Blueprint for the metrics endpoint with a unique name
metrics_blueprint = Blueprint('airflow_metrics_exporter', __name__, url_prefix='/metrics')

@metrics_blueprint.route('/')
def metrics():
    """Simple metrics endpoint that returns basic Airflow metrics in Prometheus format."""
    try:
        metrics_data = []
        
        # Add basic metrics
        metrics_data.extend([
            "# HELP airflow_up Whether Airflow is up (1) or down (0)",
            "# TYPE airflow_up gauge",
            "airflow_up 1\n"
        ])
        
        # Add DAG run metrics
        with provide_session() as session:
            # Get DAG run counts by state
            dag_status = session.query(
                DagRun.state,
                func.count(DagRun.state).label('count')
            ).group_by(DagRun.state).all()
            
            metrics_data.extend([
                "# HELP airflow_dag_run_count Number of DAG runs by state",
                "# TYPE airflow_dag_run_count gauge"
            ])
            
            for state, count in dag_status:
                metrics_data.append(f'airflow_dag_run_count{{state="{state}"}} {count}')
            
            # If no DAG runs, add default metrics
            if not dag_status:
                metrics_data.extend([
                    'airflow_dag_run_count{state="running"} 0',
                    'airflow_dag_run_count{state="success"} 0',
                    'airflow_dag_run_count{state="failed"} 0',
                ])
            
            # Add task instance metrics
            task_status = session.query(
                TaskInstance.state,
                func.count(TaskInstance.state).label('count')
            ).group_by(TaskInstance.state).all()
            
            metrics_data.extend([
                "\n# HELP airflow_task_instance_count Number of task instances by state",
                "# TYPE airflow_task_instance_count gauge"
            ])
            
            for state, count in task_status:
                metrics_data.append(f'airflow_task_instance_count{{state="{state}"}} {count}')
            
            # If no task instances, add default metrics
            if not task_status:
                metrics_data.extend([
                    'airflow_task_instance_count{state="success"} 0',
                    'airflow_task_instance_count{state="running"} 0',
                    'airflow_task_instance_count{state="failed"} 0',
                    'airflow_task_instance_count{state="up_for_retry"} 0',
                    'airflow_task_instance_count{state="upstream_failed"} 0',
                    'airflow_task_instance_count{state="skipped"} 0',
                    'airflow_task_instance_count{state="up_for_reschedule"} 0',
                    'airflow_task_instance_count{state="queued"} 0',
                    'airflow_task_instance_count{state="scheduled"} 0',
                ])
        
        return Response('\n'.join(metrics_data), mimetype='text/plain; version=0.0.4')
    except Exception as e:
        # Log the error and return a basic response
        import traceback
        error_msg = f"Error generating metrics: {str(e)}\n\n{traceback.format_exc()}"
        return Response(error_msg, status=500, mimetype='text/plain')

class SimpleMetricsExporterPlugin(AirflowPlugin):
    name = "simple_metrics_exporter"
    flask_blueprints = [metrics_blueprint]
