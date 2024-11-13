from spidermon import MonitorSuite
from spidermon.contrib.scrapy.monitors import ErrorCountMonitor, FieldCoverageMonitor, UnwantedHTTPCodesMonitor


class SingleErrorMonitorSuite(MonitorSuite):
    monitors = [
        ErrorCountMonitor,
        # FieldCoverageMonitor,
        UnwantedHTTPCodesMonitor
    ]

    monitors_failed_actions = [
        # SendSpidermonReport
    ]
