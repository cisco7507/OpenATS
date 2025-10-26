# State codes mirroring Minnetonka semantics
STATE_QUEUED = 0
STATE_RUNNING = 1
STATE_COMPLETED = 2
STATE_FAILED = 3
STATE_CANCELLED = 4
STATE_STALLED = 13

STATE_MAP = {
    STATE_QUEUED: "Queued",
    STATE_RUNNING: "Running",
    STATE_COMPLETED: "Completed",
    STATE_FAILED: "Failed",
    STATE_CANCELLED: "Cancelled",
    STATE_STALLED: "Stalled",
}
