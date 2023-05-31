from __future__ import annotations  # Python < 3.10

import logging
import sys
import time
from datetime import datetime
from typing import Any, Callable, List, Optional

from pydantic import BaseModel, Field

if sys.version_info >= (3, 10):
    from typing import TypeGuard
else:
    # Use TypeGuard from typing_extensions for python <= 3.9
    from typing_extensions import TypeGuard


#
# base
#
class TpdpException(Exception):
    """An exception for tpdp package."""


class _LoggingMixin:
    """LoggingMixin for `tpdp`."""

    DEFAULT_LOGGER_LEVEL = logging.INFO
    DEFAULT_LOGGER_STREAM = sys.stdout
    DEFAULT_LOGGER_FORMAT = "[%(asctime)s: %(levelname)s] %(name)s: %(message)s"

    def __init__(self, logger: Optional[logging.Logger] = None, **kwargs: Any) -> None:
        self._init_logger(logger)

    def _default_logger(self) -> logging.Logger:
        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(self.DEFAULT_LOGGER_LEVEL)

        handler = logging.StreamHandler(stream=self.DEFAULT_LOGGER_STREAM)
        handler.setFormatter(logging.Formatter(fmt=self.DEFAULT_LOGGER_FORMAT))
        logger.addHandler(handler)

        return logger

    def _init_logger(self, input_logger: Optional[logging.Logger]) -> None:
        if input_logger is not None:
            self.logger = input_logger
            return

        self.logger = self._default_logger()


class _BaseDataContainer(BaseModel):
    """A general class for each data container."""

    class Config:
        """Config for some data container."""

        allow_population_by_field_name = True
        smart_union = True


class _TimeResultContainer(_BaseDataContainer):
    """A general class for each container with time management."""

    start_at: Optional[datetime] = Field(default=None, description="time of start. None: object is not started.")
    finish_at: Optional[datetime] = Field(default=None, description="time of finish. None: object is not finished.")
    correct_finish: Optional[bool] = Field(
        default=None, description="is object finish without error? None: object is not finished or finished with error."
    )


#
# state
#
class State(_BaseDataContainer):
    """A general class for state of some pipeline."""


def is_state(type_: Any) -> TypeGuard[State]:
    return isinstance(type_, State)


def assert_state(type_: Any) -> State:
    if not is_state(type_):
        raise TpdpException(f"Expected {type_} to be a State type.")
    return type_


#
# step
#
class StepResult(_TimeResultContainer):
    """Container for store of step result."""

    name: str
    duration: Optional[float] = Field(
        default=None, description="the duration of finished. None: object is not finished."
    )


class Step(_LoggingMixin):
    """An abstract class for some pipeline step representation."""

    step_name: str

    def __init__(self, step_name: str, **kwargs: Any) -> None:
        super(Step, self).__init__(**kwargs)

        self.step_name = step_name

    def run(self, state: State, pipeline_abort: Optional[Callable[[], None]] = None, **kwargs: Any) -> State:
        """Run of this step and modify of input state.

        Arguments:
            state: init state.
            pipeline_abort: hook for pipeline aborting.

        """
        raise NotImplementedError


def is_step(type_: Any) -> TypeGuard[Step]:
    return isinstance(type_, Step)


def assert_step(type_: Any) -> Step:
    if not is_step(type_):
        raise TpdpException(f"Expected {type_} to be a Step type.")
    return type_


#
# pipeline
#
class PipelineResult(_TimeResultContainer):
    """Container for store of pipeline result."""

    pipeline_name: str
    steps_result: List[StepResult] = Field(default_factory=list)
    pipeline_duration: Optional[float] = Field(
        default=None, description="the duration of finished. None: object is not finished."
    )


class Pipeline(_LoggingMixin):
    """A special class with the Pipeline Design Pattern realization."""

    _pipeline_name: str
    _pipeline_abort: bool

    _ignore_exception: bool

    _pipeline_start_time: float
    _pipeline_finish_time: float
    _pipeline_duration: float

    _pipeline_start_datetime: datetime
    _pipeline_finish_datetime: datetime

    _correct_finish: bool

    _state: State
    _steps: List[Step]
    _steps_result: List[StepResult]

    def __init__(
        self,
        name: str,
        ignore_exception: bool = True,
        **kwargs: Any,
    ):
        super(Pipeline, self).__init__(**kwargs)

        self._pipeline_abort = False
        self._pipeline_name = name

        self._ignore_exception = ignore_exception

        self._steps = []
        self._steps_result = []

    def _pipeline_start_log(self) -> None:
        self.logger.info(
            'Pipeline start: pipeline_name="%s", start_at="%s"',
            self._pipeline_name,
            self._pipeline_start_datetime.isoformat(),
        )

    def _pipeline_finish_log(self) -> None:
        self.logger.info(
            'Pipeline finish: pipeline_name="%s", finish_at="%s", duration="%s"',
            self._pipeline_name,
            self._pipeline_finish_datetime.isoformat(),
            self._pipeline_duration,
        )

    def _start_pipeline(self) -> None:
        self._pipeline_start_time = time.time()
        self._pipeline_start_datetime = datetime.now()

        self._pipeline_start_log()

    def _finish_pipeline(self) -> None:
        self._pipeline_finish_time = time.time()
        self._pipeline_finish_datetime = datetime.now()
        self._pipeline_duration = self._pipeline_finish_time - self._pipeline_start_time

        self._pipeline_finish_log()

    def _get_pipeline_result(self) -> PipelineResult:
        return PipelineResult(
            pipeline_name=self._pipeline_name,
            steps_result=self._steps_result,
            pipeline_duration=self._pipeline_duration,
            start_at=self._pipeline_start_datetime,
            finish_at=self._pipeline_finish_datetime,
            correct_finish=self._correct_finish,
        )

    def _run_step(self, step: Step, **kwargs: Any) -> StepResult:
        self.logger.info('Step start: step_name="%s"', step.step_name)

        step_start_time = time.time()
        step_start_datetime = datetime.now()

        step_correct_finish = True
        error_message = ""

        try:
            self._state = step.run(self._state, pipeline_abort=self.pipeline_abort, **kwargs)
        except Exception as e:
            step_correct_finish = False

            if self._ignore_exception is True:
                error_message = str(e)
            else:
                raise e

        step_finish_time = time.time()
        step_finish_datetime = datetime.now()
        step_duration = step_finish_time - step_start_time

        result = StepResult(
            name=step.step_name,
            duration=step_duration,
            start_at=step_start_datetime,
            finish_at=step_finish_datetime,
            correct_finish=step_correct_finish,
        )

        run_msg = f'Step finish: step_name="{step.step_name}", step_duration="{step_duration:6f}"'

        if not step_correct_finish:
            run_msg += f', run_error="{error_message}"'

        self.logger.info(run_msg)

        return result

    def pipeline_abort(self) -> None:
        """Aborting the pipeline."""
        self._pipeline_abort = True

    def registry_step(self, step: Step) -> None:
        """Registry a step to pipeline."""

        assert_step(step)

        self._steps.append(step)
        self.logger.info('Step registered: step_name="%s"', step.step_name)

    def get_state(self) -> State:
        return self._state

    def run(self, init_state: State, **kwargs: Any) -> PipelineResult:
        """Run the pipeline."""

        self._start_pipeline()

        self._state = init_state
        assert_state(self._state)

        self._correct_finish = True

        if len(self._steps) == 0:
            self.logger.warning("Empty steps sequence")
            self._finish_pipeline()

            return self._get_pipeline_result()

        for step in self._steps:
            step_result = self._run_step(step, **kwargs)
            self._steps_result.append(step_result)

            if not step_result.correct_finish:
                self._correct_finish = False
                break

            if self._pipeline_abort is True:
                self.logger.info('Pipeline was aborted by a step: step_name="%s"', step.step_name)
                break

        self._finish_pipeline()
        return self._get_pipeline_result()
