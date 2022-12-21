# The Pipeline Design Pattern

**tpdp** it is the Pipeline Design Pattern realization in Python.

## Quickstart

Install with pip

```bash
pip install tpdp
```

and creating your first pipeline

```python
from tpdp import Pipeline, State, Step

class SimpleState(State):
    pipeline_name: str
    step_1_count: int = 0
    step_2_count: int = 0

init_state = SimpleState(pipeline_name="simple_pipeline")

pipeline = Pipeline(name="simple_pipeline", init_state=init_state)
log = pipeline.log

class Step1(Step):
    def run(self, state: SimpleState, **kwargs) -> SimpleState:
        state.step_1_count += 1
        log.info("step_1_count increased by 1")
        return state

class Step2(Step):
    def run(self, state: SimpleState, **kwargs) -> SimpleState:
        state.step_2_count += 1
        log.info("step_2_count increased by 1")
        return state

step_1 = Step1(name="step_1")
step_2 = Step2(name="step_2")

pipeline.registry(step_1)
pipeline.registry(step_2)
pipeline.registry(step_1)
pipeline.registry(step_2)
pipeline.registry(step_1)
pipeline.registry(step_2)
pipeline.registry(step_1)

result, final_state = pipeline.run()

print(f"final_state.step_1_count = {final_state.step_1_count}")
print(f"final_state.step_2_count = {final_state.step_2_count}")
```

You will see the following logs

```bash
[2022-12-21 17:19:54,662: INFO] tpdp.pipeline: Step registered: step_name="step_1"
[2022-12-21 17:19:54,662: INFO] tpdp.pipeline: Step registered: step_name="step_2"
[2022-12-21 17:19:54,662: INFO] tpdp.pipeline: Step registered: step_name="step_1"
[2022-12-21 17:19:54,662: INFO] tpdp.pipeline: Step registered: step_name="step_2"
[2022-12-21 17:19:54,662: INFO] tpdp.pipeline: Step registered: step_name="step_1"
[2022-12-21 17:19:54,662: INFO] tpdp.pipeline: Step registered: step_name="step_2"
[2022-12-21 17:19:54,662: INFO] tpdp.pipeline: Step registered: step_name="step_1"
[2022-12-21 17:19:54,662: INFO] tpdp.pipeline: Pipeline start: pipeline_name="simple_pipeline"
[2022-12-21 17:19:54,662: INFO] tpdp.pipeline: Step run: step_name="step_1"
[2022-12-21 17:19:54,662: INFO] tpdp.pipeline: step_1_count increased by 1
[2022-12-21 17:19:54,662: INFO] tpdp.pipeline: Step finish: step_name="step_1", step_duration="..."
[2022-12-21 17:19:54,662: INFO] tpdp.pipeline: Step run: step_name="step_2"
[2022-12-21 17:19:54,662: INFO] tpdp.pipeline: step_2_count increased by 1
[2022-12-21 17:19:54,662: INFO] tpdp.pipeline: Step finish: step_name="step_2", step_duration="..."
[2022-12-21 17:19:54,662: INFO] tpdp.pipeline: Step run: step_name="step_1"
[2022-12-21 17:19:54,662: INFO] tpdp.pipeline: step_1_count increased by 1
[2022-12-21 17:19:54,662: INFO] tpdp.pipeline: Step finish: step_name="step_1", step_duration="..."
[2022-12-21 17:19:54,662: INFO] tpdp.pipeline: Step run: step_name="step_2"
[2022-12-21 17:19:54,662: INFO] tpdp.pipeline: step_2_count increased by 1
[2022-12-21 17:19:54,662: INFO] tpdp.pipeline: Step finish: step_name="step_2", step_duration="..."
[2022-12-21 17:19:54,662: INFO] tpdp.pipeline: Step run: step_name="step_1"
[2022-12-21 17:19:54,662: INFO] tpdp.pipeline: step_1_count increased by 1
[2022-12-21 17:19:54,662: INFO] tpdp.pipeline: Step finish: step_name="step_1", step_duration="..."
[2022-12-21 17:19:54,662: INFO] tpdp.pipeline: Step run: step_name="step_2"
[2022-12-21 17:19:54,662: INFO] tpdp.pipeline: step_2_count increased by 1
[2022-12-21 17:19:54,662: INFO] tpdp.pipeline: Step finish: step_name="step_2", step_duration="..."
[2022-12-21 17:19:54,662: INFO] tpdp.pipeline: Step run: step_name="step_1"
[2022-12-21 17:19:54,662: INFO] tpdp.pipeline: step_1_count increased by 1
[2022-12-21 17:19:54,662: INFO] tpdp.pipeline: Step finish: step_name="step_1", step_duration="..."
[2022-12-21 17:19:54,662: INFO] tpdp.pipeline: Pipeline finish: pipeline_name="simple_pipeline", pipeline_duration="..."
final_state.step_1_count = 4
final_state.step_2_count = 3
```