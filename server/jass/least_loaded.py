import json
import time

"""
 This is Midd4VC's default Job Assignment Strategy (JASS).

 It assigns jobs to vehicles/infrastructure using a Least-loaded Assignment strategy.

 Strategy summary:
    - Check for any job timeouts and requeue jobs that have time out.
    - Identify vehicles/infrastructure that are currently busy processing jobs.
    - From the available vehicles/infrastructure (not busy), select those with the lowest historical load,
      i.e., those that have processed fewest jobs so far.
    - Assign each pending job to the least loaded available vehicle.
    - Publish the job assignment via MQTT to the appropriate topic for the selected vehicle.
    - If no vehicles are available, the job remains in the topic until next attempt.

    This strategy helps balance the workload evenly among vehicles over time,
    preventing some vehicles from becoming overloaded while others remain idle.
"""

def assign_jobs_least_loaded(engine):
      
    engine.check_job_timeouts()

    busy_vehicles = set(engine.jobs_in_progress.values())

    # List of available vehicles (not currently processing any job)
    available_vehicles = [v for v in engine.vehicles if v not in busy_vehicles]

    # Sort available vehicles by least load (number of jobs processed)
    available_vehicles.sort(key=lambda v: engine.vehicle_load.get(v, 0))

    while engine.jobs_queue and available_vehicles:
        job = engine.jobs_queue.pop(0)
        job_id = job["job_id"]

        # assigned_vehicle, load = sorted_vehicles[0]
        assigned_vehicle = available_vehicles.pop(0)  # Pick the first free vehicle
            
        if not assigned_vehicle:
            # No vehicle available now
            engine.jobs_queue.insert(0, job)  # put the job back in the queue
            break

        engine.jobs_in_progress[job_id] = assigned_vehicle
        engine.job_assignments[job_id] = {
            "vehicle_id": assigned_vehicle,
            "assigned_at": time.time(),
            "job_data": job
        }

        print(f"[Midd4VCServer] Assigning job {job_id} to vehicle {assigned_vehicle}")
        if engine.mqtt_client:
                engine.mqtt_client.publish(f"vc/vehicle/{assigned_vehicle}/job/assign", json.dumps(job), qos=1)
        else:
            print(f"[Midd4VCServer] MQTT client not set. Cannot assign job {job_id}.")