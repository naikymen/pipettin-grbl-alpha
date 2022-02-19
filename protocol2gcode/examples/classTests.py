class TaskEnvironment(object):
    """gcode constructor class"""

    def __init__(self, _protocol, _workspace, _platforms_in_workspace, _clearance=50):
        self.clearance = self.getClearance(_platforms_in_workspace)
        self.protocol = _protocol
        self.workspace = _workspace
        self.platformsInWorkspace = _platforms_in_workspace

    def getClearance(self, _platforms_in_workspace):
        """Supposed to get clearance level for Z axis from the workspace definition"""
        return max([platform["defaultTopPosition"] for platform in _platforms_in_workspace])


    # g = TaskEnvironment(protocol, workspace, platformsInWorkspace, clearance)
    # g._clearance = 20
    # print(g)
