import logging
import time
from datetime import datetime
from sys import stdout
from typing import Any, List, Optional, Tuple, TypeVar, cast

import pytz
from pydantic import BaseModel, Field

__all__ = [
    "StepResult",
    "PipelineResult",
    "State",
    "Step",
    "Pipeline",
    # exceptions
    "PipelineStateError",
    "PipelineRegistryError",
    # methods
    "is_state",
    "assert_state",
    "is_step",
    "assert_step",
]


class PipelineStateError(Exception):
    """An exception for some error when we have a problem for initial pipeline state."""


class PipelineRegistryError(Exception):
    """An exception for some error when we have a problem for step registry."""


class _BaseDataContainer(BaseModel):
    """A general class for each data container."""

    class Config:
        """Config for some data container."""
        allow_population_by_field_name = True
        smart_union = True
        json_encoders = {
            # custom output conversion for datetime
            datetime: lambda dt: dt.isoformat()
        }

    @classmethod
    def from_dict(cls, obj: Any):
        """Special wrapper over .parse_obj method."""
        return cls.parse_obj(obj)

    def to_dict(self):
        """Special wrapper over .dict method."""
        return self.dict(by_alias=True)


class _TimeResultContainer(_BaseDataContainer):
    """A general class for each container with time management."""

    start_at: Optional[datetime] = Field(
        default=None,
        description="time of start. None: object is not started."
    )
    finish_at: Optional[datetime] = Field(
        default=None,
        description="time of finish. None: object is not finished."
    )
    correct_finish: Optional[bool] = Field(
        default=None,
        description="is object finish without error? None: object is not finished or finished with error."
    )


#
# Pipeline State
#
class State(_BaseDataContainer):
    """A general class for state of some pipeline."""


State_T = TypeVar('State_T', bound=State)  # pylint: disable=invalid-name


def is_state(type_: Any) -> bool:
    return isinstance(type_, State)


def assert_state(type_: Any) -> State_T:  # type: ignore
    if not is_state(type_):
        raise PipelineStateError(f"Expected {type_} to be a State type.")
    return cast(State_T, type_)


#
# Pipeline Step
#
class StepResult(_TimeResultContainer):
    """Container for store of step result."""

    step_name: str
    step_duration: Optional[float] = Field(
        default=None,
        description="the duration of finished. None: object is not finished."
    )


class Step:
    """An abstract class for some pipeline step representation.

    Args:
        name: a name of step.

    """

    def __init__(self, name: str):
        self.step_name = name

    def run(self, state: State_T, **kwargs: Any) -> State_T:
        """Run of this step and modify of input state."""
        raise NotImplementedError


Step_T = TypeVar('Step_T', bound=Step)  # pylint: disable=invalid-name


def is_step(type_: Any) -> bool:
    return isinstance(type_, Step)


def assert_step(type_: Any) -> Step:
    if not is_step(type_):
        raise PipelineRegistryError(f"Expected {type_} to be a Step type.")
    return cast(Step, type_)


#
# Pipeline
#
class PipelineResult(_TimeResultContainer):
    """Container for store of pipeline result."""

    pipeline_name: str
    steps: List[StepResult] = Field(default_factory=list)
    pipeline_duration: Optional[float] = Field(
        default=None,
        description="the duration of finished. None: object is not finished."
    )


class Pipeline:
    """A special class with the Pipeline Design Pattern realization.

    Args:
        name: the name of pipeline.
        init_state: initial state of the pipeline.

    """

    def __init__(
        self,
        name: str,
        init_state: State_T,
        stream_method: Any = stdout,
        log_level: str = "INFO",
    ):
        self.pipeline_name = name

        self.log_level = log_level
        self.stream_method = stream_method

        self.log = self._init_logger()

        assert_state(init_state)

        self.state = init_state
        self.steps: List[Step] = []

    def _init_logger(self) -> logging.Logger:
        log = logging.getLogger(__name__)
        log.setLevel(self.log_level)

        handler = logging.StreamHandler(stream=self.stream_method)
        handler.setFormatter(
            logging.Formatter(fmt='[%(asctime)s: %(levelname)s] %(name)s: %(message)s')
        )
        log.addHandler(handler)

        return log

    def registry(self, step: Step_T):
        """Registry a step to pipeline."""

        assert_step(step)

        self.steps.append(step)
        self.log.info('Step registered: step_name="%s"', step.step_name)

    def run_step(self, step: Step_T, **kwargs: Any) -> StepResult:
        """Run a step."""

        self.log.info('Step run: step_name="%s"', step.step_name)
        result = StepResult(step_name=step.step_name)

        step_start_time = time.time()
        result.start_at = datetime.now().astimezone(pytz.utc)

        correct_step_finish = True
        error_message = ""

        try:
            self.state = step.run(self.state, **kwargs)
        except Exception as e:  # pylint: disable=broad-except, invalid-name
            error_message = str(e)
            correct_step_finish = False

        step_final_time = time.time() - step_start_time

        result.finish_at = datetime.now().astimezone(pytz.utc)
        result.step_duration = step_final_time
        result.correct_finish = correct_step_finish

        msg = f'Step finish: step_name="{step.step_name}", step_duration="{step_final_time:6f}"'

        if not correct_step_finish:
            msg += f', run_error="{error_message}"'

        self.log.info(msg)

        return result

    def run(self, **kwargs: Any) -> Tuple[PipelineResult, State_T]:
        """Run the pipeline."""

        self.log.info('Pipeline start: pipeline_name="%s"', self.pipeline_name)
        result = PipelineResult(pipeline_name=self.pipeline_name)

        pipeline_start_time = time.time()
        result.start_at = datetime.now().astimezone(pytz.utc)

        correct_pipeline_finish = True

        if len(self.steps) == 0:
            self.log.warning("Empty steps sequence")

        for step in self.steps:
            step_result = self.run_step(step, **kwargs)

            result.steps.append(step_result)

            if not step_result.correct_finish:
                correct_pipeline_finish = False
                break

        pipeline_final_time = time.time() - pipeline_start_time

        result.finish_at = datetime.now().astimezone(pytz.utc)
        result.pipeline_duration = pipeline_final_time
        result.correct_finish = correct_pipeline_finish

        msg = f'Pipeline finish: pipeline_name="{self.pipeline_name}", pipeline_duration="{pipeline_final_time:6f}"'

        self.log.info(msg)

        return result, self.state
