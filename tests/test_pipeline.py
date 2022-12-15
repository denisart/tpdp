import pytest

from tpdp.pipeline import Pipeline, PipelineRegistryError, PipelineStateError, State, Step, assert_state, assert_step


def test_simple_state():
    class MyState(State):
        state_name: str

    state = MyState(state_name="my_state")
    assert_state(state)

    assert state.to_dict() == {"state_name": "my_state"}


def test_invalid_state():
    class MyState:
        def __init__(self, state_name: str):
            self.state_name = state_name

    state = MyState(state_name="state")

    with pytest.raises(PipelineStateError):
        assert_state(state)


def test_invalid_step():
    class MyStep:
        pass

    step = MyStep()

    with pytest.raises(PipelineRegistryError):
        assert_step(step)


def test_simple_step():
    class MyState(State):
        state_name: str
        my_step_count: int = 0
        my_step_sum: int = 0

    class MyStep(Step):
        def run(self, state: MyState, delta: int = 0, **kwargs) -> MyState:
            """Run of this step and modify of input state."""
            state.my_step_count += 1
            state.my_step_sum += delta
            return state

    state = MyState(state_name="my_state")
    step = MyStep(name="my_step")

    state = step.run(state, delta=1)
    state = step.run(state, delta=2)
    state = step.run(state, delta=3)
    state = step.run(state, delta=4)
    state = step.run(state, delta=5)

    assert state.my_step_count == 5
    assert state.my_step_sum == 15


def test_simple_pipeline():
    """Simple scenario for using pipeline."""

    pipeline_name = "SimplePipeline"

    class SimpleState(State):
        pipeline_name: str
        step_1_count: int = 0
        step_2_count: int = 0

    class Step1(Step):
        def run(self, state: SimpleState, **kwargs) -> SimpleState:
            state.step_1_count += 1
            return state

    class Step2(Step):
        def run(self, state: SimpleState, **kwargs) -> SimpleState:
            state.step_2_count += 1
            return state

    init_state = SimpleState(pipeline_name=pipeline_name)

    step_1 = Step1(name="step_1")
    step_2 = Step2(name="step_2")

    pipeline = Pipeline(name=pipeline_name, init_state=init_state)

    pipeline.registry(step_1)
    pipeline.registry(step_2)
    pipeline.registry(step_1)
    pipeline.registry(step_2)
    pipeline.registry(step_1)
    pipeline.registry(step_2)
    pipeline.registry(step_1)

    result, final_state = pipeline.run()

    assert final_state.step_1_count == 4
    assert final_state.step_2_count == 3

    assert result.correct_finish is True
    assert len(result.steps) == 7

    for step_id in range(7):
        assert result.steps[step_id].correct_finish is True
