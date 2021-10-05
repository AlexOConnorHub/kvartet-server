import asyncio
import time
async def sample_task(task_seconds):
    print('Task takes {} seconds to complete'.format(task_seconds))
    await asyncio.sleep(task_seconds)
    return 'task has been completed'

if __name__ == '__main__':
    sample_event = asyncio.get_event_loop()
    try:
        print('Creation of tasks started')
        task_object_loop1 = sample_event.create_task(sample_task(5))
        task_object_loop2 = sample_event.create_task(sample_task(3))
        # sample_event.run_in_executor(task_object_loop)
        sample_event.run_until_complete(task_object_loop1)
    finally:
        sample_event.close()
        print("Task status: {}".format(task_object_loop1.result()))