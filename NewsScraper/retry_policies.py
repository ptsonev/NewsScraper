from tenacity import RetryCallState, retry_if_result
from zyte_api import AggressiveRetryFactory, stop_on_download_error, stop_after_uninterrupted_delay, stop_on_count


def check_if_actions_failed(result_outcome: dict) -> bool:
    for action in result_outcome.get('actions', []):
        if action.get('status') != 'success':
            return True

    if 'networkCapture' not in result_outcome.get('echoData', {}):
        return False

    if 'networkCapture' not in result_outcome:
        return True

    try:
        return result_outcome['networkCapture'][0]['interceptionStatus'].get('status') != 'success'
    except IndexError:
        pass

    return False


class RetryFactoryEx(AggressiveRetryFactory):
    retry_condition = (
            AggressiveRetryFactory.retry_condition
            | retry_if_result(check_if_actions_failed)
    )

    network_error_stop = stop_after_uninterrupted_delay(5 * 60)
    download_error_stop = stop_on_download_error(max_total=12, max_permanent=6)
    undocumented_error_stop = stop_on_count(6)

    def wait(self, retry_state: RetryCallState) -> float:
        if retry_state.outcome.exception():
            return super().wait(retry_state)

        if check_if_actions_failed(retry_state.outcome.result()):
            return self.temporary_download_error_wait(retry_state)

    def stop(self, retry_state: RetryCallState) -> bool:
        if retry_state.outcome.exception():
            return super().stop(retry_state)

        if check_if_actions_failed(retry_state.outcome.result()):
            return self.temporary_download_error_stop(retry_state)


RETRY_POLICY_EXTENDED = RetryFactoryEx().build()
