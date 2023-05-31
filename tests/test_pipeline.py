import pytest

from tpdp.pipeline import Pipeline, TpdpException, State, Step, assert_state, assert_step


def test_simple_state():
    class MyState(State):
        state_name: str

    state = MyState(state_name="my_state")
    assert_state(state)

    assert state.dict() == {"state_name": "my_state"}


def test_invalid_state():
    class MyState:
        def __init__(self, state_name: str):
            self.state_name = state_name

    state = MyState(state_name="state")

    with pytest.raises(TpdpException):
        assert_state(state)


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

    my_state = MyState(state_name="my_state")
    step = MyStep(step_name="my_step")

    my_state = step.run(my_state, delta=1)
    my_state = step.run(my_state, delta=2)
    my_state = step.run(my_state, delta=3)
    my_state = step.run(my_state, delta=4)
    my_state = step.run(my_state, delta=5)

    assert my_state.my_step_count == 5
    assert my_state.my_step_sum == 15


def test_invalid_step():
    class MyStep:
        pass

    step = MyStep()

    with pytest.raises(TpdpException):
        assert_step(step)


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

    step_1 = Step1(step_name="step_1")
    step_2 = Step2(step_name="step_2")

    pipeline = Pipeline(name=pipeline_name)

    pipeline.registry_step(step_1)
    pipeline.registry_step(step_2)
    pipeline.registry_step(step_1)
    pipeline.registry_step(step_2)
    pipeline.registry_step(step_1)
    pipeline.registry_step(step_2)
    pipeline.registry_step(step_1)

    result = pipeline.run(init_state=init_state)
    final_state = pipeline.get_state()

    assert final_state.step_1_count == 4
    assert final_state.step_2_count == 3

    assert result.correct_finish is True
    assert len(result.steps_result) == 7

    for step_id in range(7):
        assert result.steps_result[step_id].correct_finish is True

    assert pipeline._pipeline_abort is False


def test_pipeline_abort():
    """Abort pipeline from a step."""

    class Step1(Step):
        def run(self, state: State, **kwargs) -> State:
            return state

    class Step2(Step):
        def run(self, state: State, **kwargs) -> State:
            if "pipeline_abort" in kwargs:
                pipeline_abort = kwargs["pipeline_abort"]
                pipeline_abort()
            return state

    step_1 = Step1(step_name="step_1")
    step_2 = Step2(step_name="step_2")

    pipeline = Pipeline(name="SimplePipeline")

    pipeline.registry_step(step_1)
    pipeline.registry_step(step_1)
    pipeline.registry_step(step_2)
    pipeline.registry_step(step_2)
    pipeline.registry_step(step_1)

    result = pipeline.run(init_state=State())
    _ = pipeline.get_state()

    assert result.correct_finish is True
    assert len(result.steps_result) == 3

    for step_id in range(3):
        assert result.steps_result[step_id].correct_finish is True

    assert pipeline._pipeline_abort is True


class ErrorStep(Step):
    def run(self, state: State, **kwargs) -> State:
        raise ValueError()


error_step = ErrorStep(step_name="error_step")


def test_pipeline_with_error_ignore_exception():
    pipeline = Pipeline(name="PipelineWithError")

    pipeline.registry_step(error_step)
    pipeline.registry_step(error_step)

    result = pipeline.run(init_state=State())

    assert result.correct_finish is False
    assert len(result.steps_result) == 1

    assert pipeline._pipeline_abort is False


def test_pipeline_with_error_not_ignore_exception():
    pipeline = Pipeline(name="PipelineWithError", ignore_exception=False)

    pipeline.registry_step(error_step)
    pipeline.registry_step(error_step)

    with pytest.raises(ValueError):
        pipeline.run(init_state=State())
