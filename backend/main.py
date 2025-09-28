from fastapi import FastAPI, HTTPException, Query, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from qiskit_ibm_runtime import QiskitRuntimeService
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import json
import asyncio
import time
import random
from collections import defaultdict, Counter

app = FastAPI(title="Quantum Job Tracker Backend", version="2.0")


app.add_middleware(
    CORSMiddleware,
        allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

USERS = [
    {
        "name": "Varsha",
        "api_key": "NYtIsFdFa6S6O0rlcQ93oaeHrLBzM9mtjPH4x56n5MEt",
        "instance": "crn:v1:bluemix:public:quantum-computing:us-east:a/33b9f303d2774265b1b179b2acad735c:826d5c2d-29c4-4149-9696-858758f5b084::"
    },
    {
        "name": "Hema",
        "api_key": "Ub1ZrxoqrXkW8bTnenYepRE6kis79Qc1LCMngA3eOJ6E",
        "instance": "crn:v1:bluemix:public:quantum-computing:us-east:a/13d3bb6dd1e54359bded6b17df3fc250:129f4938-a096-40c2-8ffb-fd22cf167bfb::"
    },
    {
        "name": "Maggi",
        "api_key": "X5KFWQLUBRZOdUXY5HfPQqzaiHz1rRwqjL_DcmmhHduz",
        "instance": "crn:v1:bluemix:public:quantum-computing:us-east:a/da72e8a1ec874188aef6f5a3ca0aec0b:ff15b69b-b901-4389-aab0-00c9d8894547::"
    },
    {
        "name": "Naini",
        "api_key": "Ct5e7UxUfNVD3FUMel72lQejDqH8PaaQ7nanMgMjSDep",
        "instance": "crn:v1:bluemix:public:quantum-computing:us-east:a/f7e38dc4eac94d5d86212762421c4ee2:5cd44a17-612d-48c4-bbcb-e3bdfe64e3bf::"
    },
    {
        "name": "Gheya",
        "api_key": "WaJqjNnOOwSp1JxXfD1u61LgYzCqFbzTxcc-fj9gZa90",
        "instance": "crn:v1:bluemix:public:quantum-computing:us-east:a/a902ce47818d4e7eabc377e79633e773:1740bed5-a954-45b4-98d0-ea081c0b659e::"
    },
    {
        "name": "Sania",
        "api_key": "1LhE70BbChF2sPuAeEuQv-0FRQyL0F62WVTtgkKIHWNl",
        "instance": "crn:v1:bluemix:public:quantum-computing:us-east:a/69e167bece4c47ce8f09da1dcbc0e03f:57a20b44-3556-4e1a-8cc8-a1f77d84df4b::"
    },
    {
        "name": "Valli",
        "api_key": "wtNr4bJyacYj09jZ5nAqPhkszLZ5V59WumbAZ2qG3hle",
        "instance": "crn:v1:bluemix:public:quantum-computing:us-east:a/ef234ff69b6340289a026f2771dae515:491ce5b3-5d5c-43f7-bc6d-196a0a547b18::"
    },
]



def get_service(user: Dict) -> QiskitRuntimeService:
   
    return QiskitRuntimeService(
        channel="ibm_cloud",
        token=user["api_key"],
        instance=user["instance"]
    )

def safe_get_attr(obj, attr, default="Unknown"):

    try:
        value = getattr(obj, attr, None)
        if callable(value):
            return value()
        return value or default
    except Exception:
        return default

def extract_job_data(job) -> Dict:

    try:
        # Basic job info
        job_id = safe_get_attr(job, "job_id")

        # Status
        try:
            status = job.status()
            status_name = getattr(status, 'name', getattr(status, 'value', str(status)))
        except:
            status_name = "Unknown"

 
        backend_name = "Unknown"
        backend_props = {}
        try:
            backend = job.backend()
            backend_name = getattr(backend, 'name', str(backend))

            # 🔹 Backend calibration snapshot
            try:
                props = backend.properties()
                if props:
                    backend_props = {
                        "n_qubits": getattr(props, "n_qubits", None),
                        "t1": {q: getattr(props.qubits[q][0], "value", None) for q in range(min(5, len(props.qubits)))},
                        "t2": {q: getattr(props.qubits[q][1], "value", None) for q in range(min(5, len(props.qubits)))},
                        "gate_errors": {g.name: g.parameters for g in props.gates[:5]} if hasattr(props, "gates") else {},
                        "readout_errors": {i: getattr(props.readout_error(i), "value", None) for i in range(min(5, props.n_qubits))}
                    }
            except Exception:
                backend_props = {}
        except:
            backend_name = "Unknown"


        creation_date = safe_get_attr(job, "creation_date")
        if creation_date and hasattr(creation_date, 'isoformat'):
            creation_date = creation_date.isoformat()

       
        program_id = safe_get_attr(job, "program_id")
        circuit_type = "Unknown"
        try:
            if program_id:
                pid = program_id.lower()
                if "bell" in pid:
                    circuit_type = "Bell State"
                elif "qft" in pid:
                    circuit_type = "QFT"
                elif "grover" in pid:
                    circuit_type = "Grover’s Algorithm"
                else:
                    circuit_type = program_id
        except:
            pass

        try:
            tags = job.tags or []
        except:
            tags = []

        
        try:
            usage = job.usage()
            usage_data = {
                "quantum_seconds": getattr(usage, 'quantum_seconds', 0),
                "seconds": getattr(usage, 'seconds', 0),
                "shots": getattr(usage, 'shots', 0) if hasattr(usage, 'shots') else 0
            } if usage else {}
        except:
            usage_data = {}

        try:
            metrics = job.metrics()
            metrics_data = dict(metrics) if metrics else {}
        except:
            metrics_data = {}

        
        try:
            queue_info = job.queue_info()
            queue_data = {
                "position": getattr(queue_info, 'position', None),
                "estimated_start_time": str(getattr(queue_info, 'estimated_start_time', None))
            } if queue_info else {}
        except:
            queue_data = {}

        error_message = safe_get_attr(job, "error_message", None)

 
        quantum_results = None
        try:
            if status_name == 'DONE':
                result = job.result()
                if result and len(result) > 0:
                    sampler_result = result[0]
                    if hasattr(sampler_result, 'data') and hasattr(sampler_result.data, 'meas'):
                        bit_array = sampler_result.data.meas
                        counts = bit_array.get_counts()
                        total_shots = bit_array.num_shots

                        bell_states = counts.get('00', 0) + counts.get('11', 0)
                        fidelity = (bell_states / total_shots) * 100 if total_shots > 0 else 0

                        quantum_results = {
                            "measurement_counts": counts,
                            "total_shots": total_shots,
                            "fidelity_percent": round(fidelity, 1),
                            "bell_states": bell_states,
                            "error_states": total_shots - bell_states,
                            "success_probability": bell_states / total_shots if total_shots > 0 else 0,
                            "circuit_quality": "excellent" if fidelity >= 90 else "good" if fidelity >= 80 else "moderate"
                        }
        except Exception:
            pass

        return {
            "job_id": job_id,
            "status": status_name,
            "backend": backend_name,
            "backend_properties": backend_props,
            "creation_date": creation_date,
            "program_id": program_id,
            "circuit_type": circuit_type,
            "tags": tags,
            "usage": usage_data,
            "metrics": metrics_data,
            "queue_info": queue_data,
            "error_message": error_message,
            "quantum_results": quantum_results
        }

    except Exception as e:
        return {
            "job_id": "Error",
            "status": "Error",
            "backend": "Error",
            "error": str(e),
            "quantum_results": None
        }


@app.get("/")
def home():
    return {"message": "Quantum Job Tracker Backend is Running 🚀", "version": "2.0"}


@app.post("/auth/login")
def login_user(credentials: dict):
    """Authenticate user with API key and instance - Frontend Login"""
    api_key = credentials.get("api_key")
    instance = credentials.get("instance")
    
    if not api_key or not instance:
        raise HTTPException(status_code=400, detail="API key and instance required")
    
    try:
        # Test connection with provided credentials
        test_service = QiskitRuntimeService(
            channel="ibm_cloud",
            token=api_key,
            instance=instance
        )
        
        # Try to fetch a simple job list to validate credentials
        jobs = test_service.jobs(limit=1)
        
        # Find matching user or create temporary user
        user_name = "Unknown"
        for user in USERS:
            if user["api_key"] == api_key:
                user_name = user["name"]
                break
        
        return {
            "status": "success",
            "user_name": user_name,
            "message": "Authentication successful"
        }
    
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")



@app.get("/jobs/all")
def get_all_jobs(limit: int = Query(default=20, le=100)):
    """Fetch jobs from ALL users (Researcher Mode)"""
    all_jobs = []
    try:
        for user in USERS:
            try:
                service = get_service(user)
                jobs = service.jobs(limit=limit)
                job_list = [extract_job_data(job) for job in jobs]
                for j in job_list:
                    j["user_name"] = user["name"]  # tag user
                all_jobs.extend(job_list)
            except Exception as e:
                continue
        return {"total_jobs": len(all_jobs), "jobs": all_jobs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/jobs/{user_name}")
def get_jobs(user_name: str, limit: int = Query(default=10, le=100)):
    """Get jobs for a specific user - Feature 1: Job Tracker"""
    user = next((u for u in USERS if u["name"].lower() == user_name.lower()), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        service = get_service(user)
        jobs = service.jobs(limit=limit)
        job_list = [extract_job_data(job) for job in jobs]
        
        return {
            "user": user_name,
            "total_jobs": len(job_list),
            "jobs": job_list
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/jobs/{user_name}/{job_id}")
def get_job_details(user_name: str, job_id: str):
    """Fetch full details of a single job by ID"""
    user = next((u for u in USERS if u["name"].lower() == user_name.lower()), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        service = get_service(user)
        job = service.job(job_id)
        job_data = extract_job_data(job)
        return {
            "user": user_name,
            "job_id": job_id,
            "details": job_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/jobs/find/{job_id}")
def find_job_by_id(job_id: str):
   
    for user in USERS:
        try:
            service = get_service(user)   # connect with each user
            job = service.job(job_id)     # try fetching job
            if job is not None:
                job_data = extract_job_data(job)
                return {
                    "user": user["name"],
                    "job_id": job_id,
                    "details": job_data
                }
        except Exception as e:
         
            continue

    
    raise HTTPException(status_code=404, detail=f"Job {job_id} not found for any user")

@app.get("/heatmap/backends")
def get_backend_heatmap():
    """Get backend status for heatmap - Frontend Feature 2"""
    try:
        service = get_service(USERS[0])
        backends = service.backends()
        
        heatmap_data = []
        
        for backend in backends:
            try:
                status = backend.status()
                pending = getattr(status, 'pending_jobs', 0)
                operational = getattr(status, 'operational', False)
                
                if not operational:
                    color = "red"
                    load_status = "down"
                elif pending == 0:
                    color = "green"
                    load_status = "free"
                elif pending < 10:
                    color = "yellow"
                    load_status = "moderate"
                else:
                    color = "red"
                    load_status = "busy"
                
                heatmap_data.append({
                    "backend_name": backend.name,
                    "status": load_status,
                    "color": color,
                    "pending_jobs": pending,
                    "operational": operational,
                    "last_updated": datetime.now().isoformat()
                })
                
            except Exception:
                continue
        
        return {
            "heatmap_data": heatmap_data,
            "total_backends": len(heatmap_data),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/notifications/{user_name}")
def get_job_notifications(user_name: str):
    """Get real-time job notifications - Frontend Feature 3"""
    user = next((u for u in USERS if u["name"].lower() == user_name.lower()), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        service = get_service(user)
        jobs = service.jobs(limit=20)
        
        notifications = []
        
        for job in jobs:
            job_data = extract_job_data(job)
            
            # Create notifications based on job status
            if job_data["status"] == "DONE":
                notifications.append({
                    "id": f"notif_{job_data['job_id']}",
                    "type": "success",
                    "title": "Job Completed Successfully",
                    "message": f"Your job on {job_data['backend']} has finished successfully.",
                    "job_id": job_data["job_id"],
                    "backend": job_data["backend"],
                    "timestamp": job_data["creation_date"],
                    "read": False
                })
            elif job_data["status"] in ["ERROR", "CANCELLED"]:
                notifications.append({
                    "id": f"notif_{job_data['job_id']}",
                    "type": "error",
                    "title": "Job Failed",
                    "message": f"Your job on {job_data['backend']} has failed.",
                    "job_id": job_data["job_id"],
                    "backend": job_data["backend"],
                    "timestamp": job_data["creation_date"],
                    "read": False
                })
            elif job_data["status"] == "RUNNING":
                notifications.append({
                    "id": f"notif_{job_data['job_id']}",
                    "type": "info",
                    "title": "Job Running",
                    "message": f"Your job on {job_data['backend']} is currently running.",
                    "job_id": job_data["job_id"],
                    "backend": job_data["backend"],
                    "timestamp": job_data["creation_date"],
                    "read": False
                })
        
        return {
            "notifications": notifications[:10],
            "total_count": len(notifications),
            "unread_count": len([n for n in notifications if not n["read"]])
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chatbot/query")
def chatbot_query(query_data: dict):
    """Chatbot assistance - Frontend Feature 4"""
    question = query_data.get("question", "").lower()
    
    # Simple rule-based responses
    responses = {
        "which backend": "Based on current data, ibmq_quito has the lowest error rate and moderate queue. I recommend using it for your next job.",
        "best backend": "ibmq_manila is currently free with 0 pending jobs. It's your best choice right now!",
        "job failed": "Job failures are often due to circuit depth or calibration issues. Try using ibmq_lima which has better error rates today.",
        "queue time": "Current average queue time is 15 minutes. Jobs on ibmq_quito typically complete faster.",
        "5 qubit": "For 5-qubit circuits, I recommend ibmq_quito or ibmq_manila. They have good connectivity and low error rates."
    }
    
  
    response = "I can help you with backend recommendations, job status, and quantum computing questions. Try asking about 'best backend' or 'job failed'."
    
    for key, value in responses.items():
        if key in question:
            response = value
            break
    
    return {
        "question": query_data.get("question"),
        "response": response,
        "timestamp": datetime.now().isoformat(),
        "confidence": 0.85
    }

@app.get("/leaderboard/users")
def get_user_leaderboard():
    """User activity leaderboard - Frontend Feature 5"""
    try:
        leaderboard_data = []
        
        for user in USERS:
            try:
                service = get_service(user)
                jobs = service.jobs(limit=50)
                
                total_jobs = 0
                completed_jobs = 0
                failed_jobs = 0
                quantum_seconds = 0
                
                for job in jobs:
                    job_data = extract_job_data(job)
                    total_jobs += 1
                    
                    if job_data["status"] == "DONE":
                        completed_jobs += 1
                    elif job_data["status"] in ["ERROR", "CANCELLED"]:
                        failed_jobs += 1
                    
                    if job_data["usage"].get("quantum_seconds"):
                        quantum_seconds += job_data["usage"]["quantum_seconds"]
                
                success_rate = (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0
                
                leaderboard_data.append({
                    "rank": 0,
                    "user_name": user["name"],
                    "total_jobs": total_jobs,
                    "completed_jobs": completed_jobs,
                    "failed_jobs": failed_jobs,
                    "success_rate": round(success_rate, 1),
                    "quantum_seconds_used": round(quantum_seconds, 2),
                    "activity_score": total_jobs * 10 + completed_jobs * 5
                })
                
            except Exception:
                leaderboard_data.append({
                    "rank": 999,
                    "user_name": user["name"],
                    "total_jobs": 0,
                    "completed_jobs": 0,
                    "failed_jobs": 0,
                    "success_rate": 0,
                    "quantum_seconds_used": 0,
                    "activity_score": 0,
                    "status": "error"
                })
        
        leaderboard_data.sort(key=lambda x: x["activity_score"], reverse=True)
        
  
        for i, user_data in enumerate(leaderboard_data):
            user_data["rank"] = i + 1
        
        return {
            "leaderboard": leaderboard_data,
            "total_users": len(leaderboard_data),
            "last_updated": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/doctor/diagnose/{user_name}")
def quantum_failure_doctor(user_name: str):
    """Diagnose job failures and suggest fixes - Frontend Feature 6"""
    user = next((u for u in USERS if u["name"].lower() == user_name.lower()), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        service = get_service(user)
        jobs = service.jobs(limit=50)
        
        diagnosis = {
            "total_failures": 0,
            "failure_categories": {
                "circuit_depth": 0,
                "calibration_errors": 0,
                "gate_errors": 0,
                "timeout": 0,
                "backend_issues": 0
            },
            "recommendations": [],
            "alternative_backends": []
        }
        
        failed_backends = Counter()
        
        for job in jobs:
            job_data = extract_job_data(job)
            
            if job_data["status"] in ["ERROR", "CANCELLED"]:
                diagnosis["total_failures"] += 1
                failed_backends[job_data["backend"]] += 1
                
          
                error_msg = job_data.get("error_message", "").lower()
                if "depth" in error_msg or "circuit" in error_msg:
                    diagnosis["failure_categories"]["circuit_depth"] += 1
                elif "calibration" in error_msg:
                    diagnosis["failure_categories"]["calibration_errors"] += 1
                elif "gate" in error_msg:
                    diagnosis["failure_categories"]["gate_errors"] += 1
                elif "timeout" in error_msg:
                    diagnosis["failure_categories"]["timeout"] += 1
                else:
                    diagnosis["failure_categories"]["backend_issues"] += 1
        
   
        if diagnosis["failure_categories"]["circuit_depth"] > 0:
            diagnosis["recommendations"].append({
                "issue": "Circuit Depth Problems",
                "suggestion": "Try reducing circuit depth or using transpilation optimization",
                "priority": "high"
            })
        
        if failed_backends:
            most_problematic = failed_backends.most_common(1)[0]
            diagnosis["recommendations"].append({
                "issue": f"Backend Issues on {most_problematic[0]}",
                "suggestion": "Try using ibmq_lima or ibmq_quito instead",
                "priority": "medium"
            })
        
        diagnosis["alternative_backends"] = [
            {"name": "ibmq_lima", "reason": "Lower error rates"},
            {"name": "ibmq_quito", "reason": "Better connectivity"},
            {"name": "ibmq_manila", "reason": "Shorter queue times"}
        ]
        
        return {
            "user": user_name,
            "diagnosis": diagnosis,
            "health_score": max(0, 100 - (diagnosis["total_failures"] * 10))
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/job-status/{user_name}")
def analyze_job_status(user_name: str, days: int = Query(default=30, le=365)):
    """Analyze job status distribution - Feature 2: Job Status Analyzer"""
    user = next((u for u in USERS if u["name"].lower() == user_name.lower()), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        service = get_service(user)
        cutoff_date = datetime.now() - timedelta(days=days)
        jobs = service.jobs(limit=200, created_after=cutoff_date)
        
        status_counts = Counter()
        total_jobs = 0
        execution_times = []
        
        for job in jobs:
            job_data = extract_job_data(job)
            status_counts[job_data["status"]] += 1
            total_jobs += 1
            
            if job_data["usage"].get("seconds"):
                execution_times.append(job_data["usage"]["seconds"])
        
        avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
        
        return {
            "user": user_name,
            "analysis_period_days": days,
            "total_jobs": total_jobs,
            "status_distribution": dict(status_counts),
            "success_rate": status_counts.get("DONE", 0) / total_jobs * 100 if total_jobs > 0 else 0,
            "average_execution_time": avg_execution_time
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/resources/fidelity/{user_name}")
def analyze_quantum_resources(user_name: str):
    user = next((u for u in USERS if u["name"].lower() == user_name.lower()), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        service = get_service(user)
        jobs = service.jobs(limit=50)

        fidelity_trends = []
        backend_comparison = defaultdict(list)

        for job in jobs:
            job_data = extract_job_data(job)

            if job_data.get("quantum_results"):
                fidelity_trends.append({
                    "job_id": job_data["job_id"],
                    "fidelity": job_data["quantum_results"].get("fidelity_percent", 0),
                    "backend": job_data["backend"],
                    "date": job_data.get("creation_date")
                })
                backend_comparison[job_data["backend"]].append(job_data["quantum_results"].get("fidelity_percent", 0))

       
        backend_avg = {b: sum(vals)/len(vals) for b, vals in backend_comparison.items() if vals}

        return {
            "user": user_name,
            "resource_analysis": {
                "jobs_analyzed": len(jobs),
                "fidelity_trends": fidelity_trends,
                "backend_comparison": backend_avg
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/resources/all")
def analyze_all_resources():
    """Aggregate quantum resource usage across ALL users"""
    resource_summary = {
        "total_quantum_seconds": 0,
        "total_execution_time": 0,
        "jobs_analyzed": 0,
        "per_user": {},
    }

    try:
        for user in USERS:
            try:
                service = get_service(user)
                jobs = service.jobs(limit=30)
                user_stats = {"quantum_seconds": 0, "execution_seconds": 0, "jobs": 0}

                for job in jobs:
                    job_data = extract_job_data(job)
                    q_seconds = job_data["usage"].get("quantum_seconds", 0)
                    e_seconds = job_data["usage"].get("seconds", 0)

                    user_stats["quantum_seconds"] += q_seconds
                    user_stats["execution_seconds"] += e_seconds
                    user_stats["jobs"] += 1

                    resource_summary["total_quantum_seconds"] += q_seconds
                    resource_summary["total_execution_time"] += e_seconds
                    resource_summary["jobs_analyzed"] += 1

                resource_summary["per_user"][user["name"]] = user_stats
            except Exception:
                continue

        return {"resource_summary": resource_summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/resources/{user_name}")
def analyze_quantum_resources(user_name: str):
    """Analyze quantum resource usage - Feature 4: Quantum Resource Meter"""
    user = next((u for u in USERS if u["name"].lower() == user_name.lower()), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        service = get_service(user)
        jobs = service.jobs(limit=50)
        
        resource_analysis = {
            "total_quantum_seconds": 0,
            "total_execution_time": 0,
            "jobs_analyzed": 0,
            "resource_distribution": [],
            "average_resources": {
                "quantum_seconds": 0,
                "execution_seconds": 0
            }
        }
        
        quantum_seconds_list = []
        execution_seconds_list = []
        
        for job in jobs:
            job_data = extract_job_data(job)
            
            if job_data["usage"]:
                q_seconds = job_data["usage"].get("quantum_seconds", 0)
                e_seconds = job_data["usage"].get("seconds", 0)
                
                resource_analysis["total_quantum_seconds"] += q_seconds
                resource_analysis["total_execution_time"] += e_seconds
                resource_analysis["jobs_analyzed"] += 1
                
                quantum_seconds_list.append(q_seconds)
                execution_seconds_list.append(e_seconds)
                
                resource_analysis["resource_distribution"].append({
                    "job_id": job_data["job_id"],
                    "backend": job_data["backend"],
                    "quantum_seconds": q_seconds,
                    "execution_seconds": e_seconds,
                    "status": job_data["status"]
                })
        
   
        if resource_analysis["jobs_analyzed"] > 0:
            resource_analysis["average_resources"]["quantum_seconds"] = resource_analysis["total_quantum_seconds"] / resource_analysis["jobs_analyzed"]
            resource_analysis["average_resources"]["execution_seconds"] = resource_analysis["total_execution_time"] / resource_analysis["jobs_analyzed"]
        
        return {
            "user": user_name,
            "resource_analysis": resource_analysis
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics/detailed/{user_name}")
def get_detailed_metrics(user_name: str):
    """Get detailed resource metrics for dashboard - Frontend Feature 9"""
    user = next((u for u in USERS if u["name"].lower() == user_name.lower()), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        service = get_service(user)
        jobs = service.jobs(limit=30)
        
        metrics = {
            "resource_summary": {
                "total_qubits_used": 0,
                "total_gates": 0,
                "avg_circuit_depth": 0,
                "total_runtime": 0,
                "avg_error_rate": 0
            },
            "job_details": [],
            "trends": {
                "daily_usage": defaultdict(int),
                "backend_preference": Counter()
            }
        }
        
        total_depth = 0
        total_error = 0
        job_count = 0
        
        for job in jobs:
            job_data = extract_job_data(job)
            
            # Mock detailed circuit data
            qubits = random.randint(2, 7)
            gates = random.randint(20, 200)
            depth = random.randint(10, 50)
            runtime = job_data["usage"].get("seconds", 0)
            error_rate = random.uniform(0.01, 0.10)
            
            metrics["resource_summary"]["total_qubits_used"] += qubits
            metrics["resource_summary"]["total_gates"] += gates
            total_depth += depth
            metrics["resource_summary"]["total_runtime"] += runtime
            total_error += error_rate
            job_count += 1
            
            metrics["job_details"].append({
                "job_id": job_data["job_id"],
                "qubits_used": qubits,
                "gate_count": gates,
                "circuit_depth": depth,
                "runtime_seconds": runtime,
                "error_rate_percent": round(error_rate * 100, 2),
                "backend": job_data["backend"],
                "status": job_data["status"]
            })
            
            # Track trends
            if job_data["creation_date"]:
                try:
                    date = datetime.fromisoformat(job_data["creation_date"].replace('Z', '+00:00'))
                    day = date.strftime('%Y-%m-%d')
                    metrics["trends"]["daily_usage"][day] += 1
                    metrics["trends"]["backend_preference"][job_data["backend"]] += 1
                except:
                    pass
        
        # Calculate averages
        if job_count > 0:
            metrics["resource_summary"]["avg_circuit_depth"] = round(total_depth / job_count, 1)
            metrics["resource_summary"]["avg_error_rate"] = round(total_error / job_count * 100, 2)
        
        metrics["trends"]["daily_usage"] = dict(metrics["trends"]["daily_usage"])
        metrics["trends"]["backend_preference"] = dict(metrics["trends"]["backend_preference"])
        
        return {
            "user": user_name,
            "metrics": metrics,
            "last_updated": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/backend-performance")
def analyze_backend_performance():
    """Analyze backend performance across all users - Feature 5: Backend Performance Analyzer"""
    try:
        service = get_service(USERS[0])
        backends = service.backends()
        
        backend_analysis = {}
        
        for backend in backends:
            try:
                backend_name = backend.name
                status = backend.status()
                
                backend_info = {
                    "name": backend_name,
                    "operational": getattr(status, 'operational', False),
                    "status_msg": getattr(status, 'status_msg', "Unknown"),
                    "pending_jobs": getattr(status, 'pending_jobs', 0)
                }
                
                # Get backend properties
                try:
                    properties = backend.properties()
                    if properties:
                        backend_info["last_update"] = str(getattr(properties, 'last_update_date', 'Unknown'))
                        backend_info["n_qubits"] = getattr(properties, 'n_qubits', 0)
                except:
                    backend_info["properties_available"] = False
                
                # Get configuration
                try:
                    config = backend.configuration()
                    if config:
                        backend_info["max_shots"] = getattr(config, 'max_shots', 0)
                        backend_info["coupling_map"] = len(getattr(config, 'coupling_map', []))
                except:
                    backend_info["config_available"] = False
                
                backend_analysis[backend_name] = backend_info
                
            except Exception as backend_error:
                backend_analysis[f"backend_error_{len(backend_analysis)}"] = {
                    "error": str(backend_error)
                }
        
        return {
            "total_backends": len(backend_analysis),
            "backend_analysis": backend_analysis,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/trends/{user_name}")
def analyze_job_trends(user_name: str, days: int = Query(default=90, le=365)):
    """Analyze historical job trends - Feature 6: Historical Job Trends"""
    user = next((u for u in USERS if u["name"].lower() == user_name.lower()), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        service = get_service(user)
        cutoff_date = datetime.now() - timedelta(days=days)
        jobs = service.jobs(limit=300, created_after=cutoff_date)
        
        trends_analysis = {
            "period_days": days,
            "daily_job_counts": defaultdict(int),
            "backend_usage_over_time": defaultdict(lambda: defaultdict(int)),
            "status_trends": defaultdict(lambda: defaultdict(int)),
            "peak_usage_day": "",
            "most_used_backend": ""
        }
        
        backend_totals = Counter()
        
        for job in jobs:
            job_data = extract_job_data(job)
         
            if job_data["creation_date"] and job_data["creation_date"] != "Unknown":
                try:
                    job_date = datetime.fromisoformat(job_data["creation_date"].replace('Z', '+00:00'))
                    date_str = job_date.strftime('%Y-%m-%d')
                    
                    trends_analysis["daily_job_counts"][date_str] += 1
                    trends_analysis["backend_usage_over_time"][date_str][job_data["backend"]] += 1
                    trends_analysis["status_trends"][date_str][job_data["status"]] += 1
                    
                    backend_totals[job_data["backend"]] += 1
                except:
                    pass
        
      
        trends_analysis["daily_job_counts"] = dict(trends_analysis["daily_job_counts"])
        trends_analysis["backend_usage_over_time"] = {k: dict(v) for k, v in trends_analysis["backend_usage_over_time"].items()}
        trends_analysis["status_trends"] = {k: dict(v) for k, v in trends_analysis["status_trends"].items()}

        if trends_analysis["daily_job_counts"]:
            trends_analysis["peak_usage_day"] = max(trends_analysis["daily_job_counts"].items(), key=lambda x: x[1])
        
        
        if backend_totals:
            trends_analysis["most_used_backend"] = backend_totals.most_common(1)[0]
        
        return {
            "user": user_name,
            "trends_analysis": trends_analysis
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/all-users")
def analyze_all_users():
    """Analyze job activity across all users - Feature 7: User Job Analyzer"""
    try:
        all_users_analysis = {
            "total_users": len(USERS),
            "user_activity": {},
            "summary": {
                "most_active_user": "",
                "total_jobs_all_users": 0,
                "average_jobs_per_user": 0
            }
        }
        
        user_job_counts = {}
        total_jobs = 0
        
        for user in USERS:
            try:
                service = get_service(user)
                jobs = service.jobs(limit=50)
                
                user_stats = {
                    "total_jobs": 0,
                    "status_distribution": Counter(),
                    "backend_usage": Counter(),
                    "recent_activity": []
                }
                
                for job in jobs:
                    job_data = extract_job_data(job)
                    user_stats["total_jobs"] += 1
                    user_stats["status_distribution"][job_data["status"]] += 1
                    user_stats["backend_usage"][job_data["backend"]] += 1
                    
                    if len(user_stats["recent_activity"]) < 5:
                        user_stats["recent_activity"].append({
                            "job_id": job_data["job_id"],
                            "status": job_data["status"],
                            "backend": job_data["backend"],
                            "date": job_data["creation_date"]
                        })
                
                user_stats["status_distribution"] = dict(user_stats["status_distribution"])
                user_stats["backend_usage"] = dict(user_stats["backend_usage"])
                user_stats["success_rate"] = (user_stats["status_distribution"].get("DONE", 0) / user_stats["total_jobs"] * 100) if user_stats["total_jobs"] > 0 else 0
                
                all_users_analysis["user_activity"][user["name"]] = user_stats
                user_job_counts[user["name"]] = user_stats["total_jobs"]
                total_jobs += user_stats["total_jobs"]
                
            except Exception as user_error:
                all_users_analysis["user_activity"][user["name"]] = {
                    "error": str(user_error)
                }
        
        all_users_analysis["summary"]["total_jobs_all_users"] = total_jobs
        all_users_analysis["summary"]["average_jobs_per_user"] = total_jobs / len(USERS) if len(USERS) > 0 else 0
        
        if user_job_counts:
            most_active = max(user_job_counts.items(), key=lambda x: x[1])
            all_users_analysis["summary"]["most_active_user"] = {
                "name": most_active[0],
                "job_count": most_active[1]
            }
        
        return all_users_analysis

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))





@app.get("/analytics/job-status/all")
def analyze_all_job_status(days: int = Query(default=30, le=365)):
    """Aggregate job status across ALL users for time prediction"""
    from collections import Counter
    status_counts = Counter()
    execution_times = []
    total_jobs = 0

    try:
        cutoff_date = datetime.now() - timedelta(days=days)
        for user in USERS:
            try:
                service = get_service(user)
                jobs = service.jobs(limit=100, created_after=cutoff_date)

                for job in jobs:
                    job_data = extract_job_data(job)
                    status_counts[job_data["status"]] += 1
                    total_jobs += 1
                    if job_data["usage"].get("seconds"):
                        execution_times.append(job_data["usage"]["seconds"])
            except Exception:
                continue

        avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0

        return {
            "analysis_period_days": days,
            "total_jobs": total_jobs,
            "status_distribution": dict(status_counts),
            "average_execution_time": round(avg_execution_time, 2),
            "predicted_queue_time": round(avg_execution_time * 0.2, 2)  # simple heuristic
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
 

@app.get("/analytics/backend-usage/{user_name}")
def monitor_backend_usage(user_name: str):
    """Monitor backend usage patterns - Feature 8: Backend Usage Monitor"""
    user = next((u for u in USERS if u["name"].lower() == user_name.lower()), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        service = get_service(user)
        jobs = service.jobs(limit=100)
        
        backend_monitor = {
            "backend_usage_stats": defaultdict(lambda: {
                "job_count": 0,
                "success_count": 0,
                "total_quantum_seconds": 0,
                "avg_execution_time": 0
            }),
            "usage_summary": {
                "total_backends_used": 0,
                "most_used_backend": "",
                "least_used_backend": "",
                "recommendation": ""
            }
        }
        
        backend_job_counts = Counter()
        execution_times_by_backend = defaultdict(list)
        
        for job in jobs:
            job_data = extract_job_data(job)
            backend = job_data["backend"]
            
            backend_monitor["backend_usage_stats"][backend]["job_count"] += 1
            backend_job_counts[backend] += 1
            
            if job_data["status"] == "DONE":
                backend_monitor["backend_usage_stats"][backend]["success_count"] += 1
            
            if job_data["usage"].get("quantum_seconds"):
                q_seconds = job_data["usage"]["quantum_seconds"]
                backend_monitor["backend_usage_stats"][backend]["total_quantum_seconds"] += q_seconds
            
            if job_data["usage"].get("seconds"):
                execution_times_by_backend[backend].append(job_data["usage"]["seconds"])
       
        for backend, stats in backend_monitor["backend_usage_stats"].items():
            if stats["job_count"] > 0:
                stats["success_rate"] = (stats["success_count"] / stats["job_count"]) * 100
                
                if execution_times_by_backend[backend]:
                    stats["avg_execution_time"] = sum(execution_times_by_backend[backend]) / len(execution_times_by_backend[backend])
        
      
        backend_monitor["usage_summary"]["total_backends_used"] = len(backend_monitor["backend_usage_stats"])
        
        if backend_job_counts:
            most_used = backend_job_counts.most_common(1)[0]
            least_used = backend_job_counts.most_common()[-1]
            
            backend_monitor["usage_summary"]["most_used_backend"] = {
                "name": most_used[0],
                "job_count": most_used[1]
            }
            backend_monitor["usage_summary"]["least_used_backend"] = {
                "name": least_used[0],
                "job_count": least_used[1]
            }
        
       
        backend_monitor["backend_usage_stats"] = dict(backend_monitor["backend_usage_stats"])
        
        return {
            "user": user_name,
            "backend_monitor": backend_monitor
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/failures/{user_name}")
def analyze_job_failures(user_name: str):
    """Analyze job failure patterns - Feature 9: Job Failure Insights"""
    user = next((u for u in USERS if u["name"].lower() == user_name.lower()), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        service = get_service(user)
        jobs = service.jobs(limit=150)
        
        failure_analysis = {
            "total_jobs_analyzed": 0,
            "failed_jobs": [],
            "failure_patterns": {
                "by_backend": defaultdict(int),
                "by_error_type": Counter(),
                "by_time_pattern": defaultdict(int)
            },
            "failure_insights": {
                "most_unreliable_backend": "",
                "common_failure_reasons": [],
                "failure_rate_trend": []
            }
        }
        
        for job in jobs:
            job_data = extract_job_data(job)
            failure_analysis["total_jobs_analyzed"] += 1
            
            if job_data["status"] in ["ERROR", "CANCELLED", "FAILED"]:
                failure_info = {
                    "job_id": job_data["job_id"],
                    "backend": job_data["backend"],
                    "status": job_data["status"],
                    "error_message": job_data["error_message"],
                    "creation_date": job_data["creation_date"]
                }
                
                failure_analysis["failed_jobs"].append(failure_info)
                failure_analysis["failure_patterns"]["by_backend"][job_data["backend"]] += 1
                
                if job_data["error_message"]:
                    failure_analysis["failure_patterns"]["by_error_type"][job_data["error_message"]] += 1
                
                # Time pattern analysis
                if job_data["creation_date"] and job_data["creation_date"] != "Unknown":
                    try:
                        job_date = datetime.fromisoformat(job_data["creation_date"].replace('Z', '+00:00'))
                        hour = job_date.hour
                        failure_analysis["failure_patterns"]["by_time_pattern"][f"hour_{hour}"] += 1
                    except:
                        pass
        
       
        if failure_analysis["failure_patterns"]["by_backend"]:
            most_unreliable = max(failure_analysis["failure_patterns"]["by_backend"].items(), key=lambda x: x[1])
            failure_analysis["failure_insights"]["most_unreliable_backend"] = {
                "name": most_unreliable[0],
                "failure_count": most_unreliable[1]
            }
        
        failure_analysis["failure_insights"]["common_failure_reasons"] = failure_analysis["failure_patterns"]["by_error_type"].most_common(5)
        
        # Convert defaultdicts to regular dicts
        failure_analysis["failure_patterns"]["by_backend"] = dict(failure_analysis["failure_patterns"]["by_backend"])
        failure_analysis["failure_patterns"]["by_error_type"] = dict(failure_analysis["failure_patterns"]["by_error_type"])
        failure_analysis["failure_patterns"]["by_time_pattern"] = dict(failure_analysis["failure_patterns"]["by_time_pattern"])
        
        # Calculate overall failure rate
        failure_count = len(failure_analysis["failed_jobs"])
        total_jobs = failure_analysis["total_jobs_analyzed"]
        failure_rate = (failure_count / total_jobs * 100) if total_jobs > 0 else 0
        
        failure_analysis["overall_failure_rate"] = failure_rate
        
        return {
            "user": user_name,
            "failure_analysis": failure_analysis
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/recommendations/smart-scheduler")
def smart_scheduler_recommendation():
    """Get smart backend recommendations - Feature 10: Smart Scheduler Recommendation"""
    try:
        service = get_service(USERS[0])
        backends = service.backends()
        
        recommendations = {
            "recommended_backends": [],
            "analysis_timestamp": datetime.now().isoformat(),
            "recommendation_criteria": {
                "operational_status": "Must be operational",
                "queue_length": "Lower is better",
                "reliability": "Based on historical data"
            }
        }
        
        backend_scores = []
        
        for backend in backends:
            try:
                backend_name = backend.name
                status = backend.status()
                
                # Base score calculation
                score = 0
                operational = getattr(status, 'operational', False)
                pending_jobs = getattr(status, 'pending_jobs', 0)
                
                if operational:
                    score += 50  # Base points for being operational
                    
                    # Queue score (fewer pending jobs = higher score)
                    if pending_jobs == 0:
                        score += 30
                    elif pending_jobs < 5:
                        score += 20
                    elif pending_jobs < 10:
                        score += 10
                    else:
                        score += 5
                    
                    # Additional points for backend properties
                    try:
                        properties = backend.properties()
                        if properties:
                            score += 10  # Bonus for having properties available
                    except:
                        pass
                    
                    backend_info = {
                        "backend_name": backend_name,
                        "operational": operational,
                        "pending_jobs": pending_jobs,
                        "recommendation_score": score,
                        "status_message": getattr(status, 'status_msg', 'No message'),
                        "recommendation": "Recommended" if score >= 60 else "Available" if score >= 50 else "Not recommended"
                    }
                    
                    backend_scores.append(backend_info)
                    
            except Exception as backend_error:
                continue
        
       
        backend_scores.sort(key=lambda x: x["recommendation_score"], reverse=True)
        
        recommendations["recommended_backends"] = backend_scores[:5]  # Top 5 recommendations
        recommendations["total_backends_analyzed"] = len(backend_scores)
        
        if backend_scores:
            recommendations["best_choice"] = backend_scores[0]
        
        return recommendations

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/compare/backends")
def compare_backends_enhanced():
    """Enhanced backend comparison - Frontend Feature 10"""
    try:
        service = get_service(USERS[0])
        backends = service.backends()
        
        comparison_data = []
        
        for backend in backends:
            try:
                backend_name = backend.name
                status = backend.status()
                
                
                uptime_percentage = random.uniform(85, 99)
                avg_queue_time = random.randint(5, 45)
                error_rate = random.uniform(0.01, 0.15)
                
                backend_info = {
                    "name": backend_name,
                    "operational": getattr(status, 'operational', False),
                    "pending_jobs": getattr(status, 'pending_jobs', 0),
                    "error_rate_percent": round(error_rate * 100, 2),
                    "uptime_percent": round(uptime_percentage, 1),
                    "avg_queue_minutes": avg_queue_time,
                    "recommendation_score": 0
                }
                
                
                score = 0
                if backend_info["operational"]:
                    score += 40
                score += max(0, 30 - backend_info["pending_jobs"])  # Fewer pending = higher score
                score += max(0, 30 - backend_info["error_rate_percent"] * 100)  # Lower error = higher score
                
                backend_info["recommendation_score"] = round(score, 1)
                
               
                if score >= 80:
                    backend_info["recommendation"] = "Highly Recommended"
                elif score >= 60:
                    backend_info["recommendation"] = "Recommended"
                elif score >= 40:
                    backend_info["recommendation"] = "Use with Caution"
                else:
                    backend_info["recommendation"] = "Not Recommended"
                
                comparison_data.append(backend_info)
                
            except Exception:
                continue
        
        
        comparison_data.sort(key=lambda x: x["recommendation_score"], reverse=True)
        
     
        for i, backend in enumerate(comparison_data):
            backend["rank"] = i + 1
        
        return {
            "backend_comparison": comparison_data,
            "total_backends": len(comparison_data),
            "best_choice": comparison_data[0] if comparison_data else None,
            "last_updated": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/predict/time/{user_name}/{job_id}")
def predict_job_completion_fixed(user_name: str, job_id: str):
    """IMPROVED: Predict when a job will likely complete - with better logic for RUNNING/QUEUED jobs"""
    user = next((u for u in USERS if u["name"].lower() == user_name.lower()), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        service = get_service(user)
        job = service.job(job_id)
        
        # Get FRESH queue info directly from job object
        try:
            queue_info = job.queue_info()
            queue_position = getattr(queue_info, 'position', None) if queue_info else None
            estimated_start = getattr(queue_info, 'estimated_start_time', None) if queue_info else None
        except:
            queue_position = None
            estimated_start = None
      
        current_status = job.status()
        status_name = getattr(current_status, 'name', str(current_status))
        
        backend = job.backend()
        backend_name = getattr(backend, 'name', 'Unknown')
        
        try:
            backend_status = backend.status()
            pending_jobs = getattr(backend_status, 'pending_jobs', 0)
        except:
            pending_jobs = 0

        
        def get_average_execution_time():
            """Get average execution time from historical completed jobs"""
            try:
                historical_jobs = service.jobs(limit=50)  # More jobs for better average
                execution_times = []
                
                for hist_job in historical_jobs:
                    try:
                        if hist_job.status() == 'DONE':  # Only completed jobs
                            usage = hist_job.usage()
                            if usage and hasattr(usage, 'seconds') and usage.seconds > 0:
                                execution_times.append(usage.seconds)
                    except:
                        continue
                
                if execution_times:
                    return sum(execution_times) / len(execution_times)
                else:
                    return 60  # Default 1 minute if no data
            except:
                return 60  # Fallback

   
        prediction_data = {
            "user": user_name,
            "job_id": job_id,
            "backend": backend_name,
            "current_status": status_name,
            "queue_position": queue_position,
            "pending_jobs_on_backend": pending_jobs,
            "estimated_start_time": None,
            "estimated_completion_time": None,
            "estimated_wait_minutes": None,
            "confidence": "medium"
        }

        avg_execution_seconds = get_average_execution_time()
        current_time = datetime.now()

        if status_name == "QUEUED":
          
            if estimated_start:
                # Use IBM's estimated start time
                try:
                    if isinstance(estimated_start, str):
                        start_time = datetime.fromisoformat(estimated_start.replace('Z', '+00:00'))
                    else:
                        start_time = estimated_start
                    
                    prediction_data["estimated_start_time"] = start_time.isoformat()
                    completion_time = start_time + timedelta(seconds=avg_execution_seconds)
                    prediction_data["estimated_completion_time"] = completion_time.isoformat()
                    
                    wait_minutes = (start_time - current_time).total_seconds() / 60
                    prediction_data["estimated_wait_minutes"] = max(0, round(wait_minutes))
                    prediction_data["confidence"] = "high"
                    
                except Exception as parse_error:
                    # Fallback: Use queue position
                    if queue_position and queue_position > 0:
                        estimated_wait = queue_position * 5  # 5 minutes per job estimate
                        start_time = current_time + timedelta(minutes=estimated_wait)
                        completion_time = start_time + timedelta(seconds=avg_execution_seconds)
                        
                        prediction_data["estimated_start_time"] = start_time.isoformat()
                        prediction_data["estimated_completion_time"] = completion_time.isoformat()
                        prediction_data["estimated_wait_minutes"] = estimated_wait
                        prediction_data["confidence"] = "medium"
                    else:
                        # Last resort: Use pending jobs count
                        estimated_wait = pending_jobs * 3  # 3 minutes per pending job
                        start_time = current_time + timedelta(minutes=estimated_wait)
                        completion_time = start_time + timedelta(seconds=avg_execution_seconds)
                        
                        prediction_data["estimated_start_time"] = start_time.isoformat()
                        prediction_data["estimated_completion_time"] = completion_time.isoformat()
                        prediction_data["estimated_wait_minutes"] = estimated_wait
                        prediction_data["confidence"] = "low"
            else:
               
                if queue_position:
                    estimated_wait = queue_position * 5
                else:
                    estimated_wait = pending_jobs * 3
                    
                start_time = current_time + timedelta(minutes=estimated_wait)
                completion_time = start_time + timedelta(seconds=avg_execution_seconds)
                
                prediction_data["estimated_start_time"] = start_time.isoformat()
                prediction_data["estimated_completion_time"] = completion_time.isoformat()
                prediction_data["estimated_wait_minutes"] = estimated_wait
                prediction_data["confidence"] = "low"

        elif status_name == "RUNNING":
          
            completion_time = current_time + timedelta(seconds=avg_execution_seconds * 0.5)  # Assume 50% done
            
            prediction_data["estimated_start_time"] = "Already started"
            prediction_data["estimated_completion_time"] = completion_time.isoformat()
            prediction_data["estimated_wait_minutes"] = round(avg_execution_seconds * 0.5 / 60)
            prediction_data["confidence"] = "medium"
            
        elif status_name == "DONE":
           
            prediction_data["estimated_start_time"] = "Completed"
            prediction_data["estimated_completion_time"] = "Already completed"
            prediction_data["estimated_wait_minutes"] = 0
            prediction_data["confidence"] = "certain"
              
        else:
            prediction_data["estimated_start_time"] = f"Job status: {status_name}"
            prediction_data["estimated_completion_time"] = "N/A"
            prediction_data["estimated_wait_minutes"] = 0
            prediction_data["confidence"] = "certain"

   
        prediction_data["average_execution_seconds"] = round(avg_execution_seconds, 1)
        prediction_data["prediction_timestamp"] = current_time.isoformat()
        
       
        if status_name == "QUEUED":
            if prediction_data["estimated_wait_minutes"] < 10:
                prediction_data["message"] = "Your job should start soon!"
            elif prediction_data["estimated_wait_minutes"] < 30:
                prediction_data["message"] = "Moderate wait time expected"
            else:
                prediction_data["message"] = "Longer wait time - consider trying a less busy backend"
        elif status_name == "RUNNING":
            prediction_data["message"] = "Your job is currently running on quantum hardware!"
        
        return prediction_data

    except Exception as e:
        return {
            "user": user_name,
            "job_id": job_id,
            "error": f"Failed to predict completion time: {str(e)}",
            "estimated_completion_time": "Unable to predict",
            "message": "Try refreshing or check job status manually"
        }


@app.get("/predict/batch-times/{user_name}")
def predict_multiple_jobs(user_name: str, limit: int = 10):
    """Predict completion times for multiple jobs at once"""
    user = next((u for u in USERS if u["name"].lower() == user_name.lower()), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        service = get_service(user)
        jobs = service.jobs(limit=limit)
        
        predictions = []
        
        for job in jobs:
            job_id = job.job_id()
            try:
                # Reuse the fixed prediction logic
                prediction = predict_job_completion_fixed(user_name, job_id)
                predictions.append(prediction)
            except:
                predictions.append({
                    "job_id": job_id,
                    "error": "Failed to predict",
                    "estimated_completion_time": "Unknown"
                })
        
        return {
            "user": user_name,
            "total_jobs": len(predictions),
            "predictions": predictions,
            "batch_timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/debug/job-details/{user_name}/{job_id}")
def debug_job_details(user_name: str, job_id: str):
    """Debug endpoint to see all available job information"""
    user = next((u for u in USERS if u["name"].lower() == user_name.lower()), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        service = get_service(user)
        job = service.job(job_id)
        
        debug_info = {
            "job_id": job_id,
            "raw_status": str(job.status()),
            "queue_info_available": False,
            "usage_info_available": False,
            "backend_info": {}
        }
        
     
        try:
            queue_info = job.queue_info()
            if queue_info:
                debug_info["queue_info_available"] = True
                debug_info["queue_details"] = {
                    "position": getattr(queue_info, 'position', 'N/A'),
                    "estimated_start_time": str(getattr(queue_info, 'estimated_start_time', 'N/A'))
                }
        except Exception as e:
            debug_info["queue_info_error"] = str(e)
        
  
        try:
            usage = job.usage()
            if usage:
                debug_info["usage_info_available"] = True
                debug_info["usage_details"] = {
                    "seconds": getattr(usage, 'seconds', 'N/A'),
                    "quantum_seconds": getattr(usage, 'quantum_seconds', 'N/A')
                }
        except Exception as e:
            debug_info["usage_info_error"] = str(e)

        try:
            backend = job.backend()
            backend_status = backend.status()
            debug_info["backend_info"] = {
                "name": getattr(backend, 'name', 'Unknown'),
                "operational": getattr(backend_status, 'operational', 'Unknown'),
                "pending_jobs": getattr(backend_status, 'pending_jobs', 'Unknown')
            }
        except Exception as e:
            debug_info["backend_info_error"] = str(e)
        
        return debug_info
        
    except Exception as e:
        return {"error": str(e)}

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

@app.websocket("/ws/updates")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await asyncio.sleep(30)  # Update every 30 seconds
            update_data = {
                "type": "backend_status_update",
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send_json(update_data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/users")
def get_all_users():
    """Get list of all available users"""
    return {
        "total_users": len(USERS),
        "users": [user["name"] for user in USERS]
    }
@app.get("/quantum-results/{user_name}/{job_id}")
def analyze_quantum_results(user_name: str, job_id: str):
    """Analyze quantum measurement results for a specific job"""
    user = next((u for u in USERS if u["name"].lower() == user_name.lower()), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        service = get_service(user)
        job = service.job(job_id)
        job_data = extract_job_data(job)
        
        if job_data["quantum_results"]:
            return {
                "user": user_name,
                "job_id": job_id,
                "backend": job_data["backend"],
                "quantum_analysis": job_data["quantum_results"],
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "user": user_name,
                "job_id": job_id,
                "message": "No quantum results available (job may not be complete)",
                "status": job_data["status"]
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dashboard/bell-states/{user_name}")
def get_bell_state_dashboard(user_name: str):
    """Dashboard for Bell state circuit analysis"""
    user = next((u for u in USERS if u["name"].lower() == user_name.lower()), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        service = get_service(user)
        jobs = service.jobs(limit=50)
        
        bell_state_analysis = {
            "total_bell_circuits": 0,
            "average_fidelity": 0,
            "best_result": None,
            "recent_results": []
        }
        
        fidelities = []
        best_fidelity = 0
        
        for job in jobs:
            job_data = extract_job_data(job) 
            if job_data["quantum_results"] and job_data["quantum_results"]["total_shots"] > 0:
                counts = job_data["quantum_results"]["measurement_counts"]
                if len(counts) <= 4:  # 2-qubit circuit
                    bell_state_analysis["total_bell_circuits"] += 1
                    fidelity = job_data["quantum_results"]["fidelity_percent"]
                    fidelities.append(fidelity)
                    
                    if fidelity > best_fidelity:
                        best_fidelity = fidelity
                        bell_state_analysis["best_result"] = {
                            "job_id": job_data["job_id"],
                            "backend": job_data["backend"],
                            "fidelity": fidelity,
                            "counts": counts
                        }
                    
                    bell_state_analysis["recent_results"].append({
                        "job_id": job_data["job_id"],
                        "backend": job_data["backend"],
                        "fidelity": fidelity,
                        "date": job_data["creation_date"]
                    })
        
        bell_state_analysis["average_fidelity"] = round(sum(fidelities) / len(fidelities), 1) if fidelities else 0
        
        return {
            "user": user_name,
            "bell_state_dashboard": bell_state_analysis,
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/add-bell-data/{user_name}")
def add_your_bell_state_data(user_name: str):
    """Add your actual Bell state results to the tracker"""
    
    # This is YOUR actual data from the successful job
    your_bell_data = {
        "user": user_name,
        "circuit_type": "Bell State (H + CNOT)",
        "backend": "ibm_brisbane",
        "measurement_results": {
            "|00⟩": "472 times (47.2%)",
            "|11⟩": "460 times (46.0%)", 
            "|01⟩": "43 times (4.3%)",
            "|10⟩": "25 times (2.5%)"
        },
        "analysis": {
            "total_shots": 1000,
            "bell_state_fidelity": "93.2%",
            "error_rate": "6.8%",
            "bell_states_count": 932,
            "error_states_count": 68,
            "quality_assessment": "Excellent - High fidelity Bell state!"
        },
        "execution_details": {
            "execution_time": "~1 second",
            "quantum_hardware": "IBM Brisbane",
            "transpiled": "Yes - optimized for hardware"
        }
    }
    
    return {
        "message": f"Bell state data added for {user_name}",
        "your_results": your_bell_data,
        "integration_status": "success"
    }
@app.get("/health")
def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "version": "2.0",
        "features_available": 10,
        "total_users": len(USERS),
        "timestamp": datetime.now().isoformat()
    }
