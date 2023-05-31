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

pipeline = Pipeline(name="simple_pipeline")

class Step1(Step):
    def run(self, state: SimpleState, **kwargs) -> SimpleState:
        state.step_1_count += 1
        self.logger.info("step_1_count increased by 1")
        return state

class Step2(Step):
    def run(self, state: SimpleState, **kwargs) -> SimpleState:
        state.step_2_count += 1
        self.logger.info("step_2_count increased by 1")
        return state

step_1 = Step1(step_name="step_1")
step_2 = Step2(step_name="step_2")

pipeline.registry_step(step_1)
pipeline.registry_step(step_2)
pipeline.registry_step(step_1)
pipeline.registry_step(step_2)
pipeline.registry_step(step_1)
pipeline.registry_step(step_2)
pipeline.registry_step(step_1)

result = pipeline.run(init_state=init_state)
final_state = pipeline.get_state()

print(f"final_state.step_1_count = {final_state.step_1_count}")
print(f"final_state.step_2_count = {final_state.step_2_count}")
```

You will see the following logs

```bash
[...: INFO] Pipeline: Step registered: step_name="step_1"
[...: INFO] Pipeline: Step registered: step_name="step_2"
[...: INFO] Pipeline: Step registered: step_name="step_1"
[...: INFO] Pipeline: Step registered: step_name="step_2"
[...: INFO] Pipeline: Step registered: step_name="step_1"
[...: INFO] Pipeline: Step registered: step_name="step_2"
[...: INFO] Pipeline: Step registered: step_name="step_1"
[...: INFO] Pipeline: Pipeline start: pipeline_name="simple_pipeline", start_at="..."
[...: INFO] Pipeline: Step start: step_name="step_1"
[...: INFO] Step1: step_1_count increased by 1
[...: INFO] Pipeline: Step finish: step_name="step_1", step_duration="0.000024"
[...: INFO] Pipeline: Step start: step_name="step_2"
[...: INFO] Step2: step_2_count increased by 1
[...: INFO] Pipeline: Step finish: step_name="step_2", step_duration="0.000020"
[...: INFO] Pipeline: Step start: step_name="step_1"
[...: INFO] Step1: step_1_count increased by 1
[...: INFO] Pipeline: Step finish: step_name="step_1", step_duration="0.000016"
[...: INFO] Pipeline: Step start: step_name="step_2"
[...: INFO] Step2: step_2_count increased by 1
[...: INFO] Pipeline: Step finish: step_name="step_2", step_duration="0.000016"
[...: INFO] Pipeline: Step start: step_name="step_1"
[...: INFO] Step1: step_1_count increased by 1
[...: INFO] Pipeline: Step finish: step_name="step_1", step_duration="0.000016"
[...: INFO] Pipeline: Step start: step_name="step_2"
[...: INFO] Step2: step_2_count increased by 1
[...: INFO] Pipeline: Step finish: step_name="step_2", step_duration="0.000016"
[...: INFO] Pipeline: Step start: step_name="step_1"
[...: INFO] Step1: step_1_count increased by 1
[...: INFO] Pipeline: Step finish: step_name="step_1", step_duration="0.000023"
[...: INFO] Pipeline: Pipeline finish: pipeline_name="simple_pipeline", finish_at="...", duration="0.0005033016204833984"
final_state.step_1_count = 4
final_state.step_2_count = 3
```