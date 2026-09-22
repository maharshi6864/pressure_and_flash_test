class CurrentObjects:
    current_proof_id = None
    current_test_id = None
    latest_origin_frame = None
    latest_maximum_x_frame = None
    latest_maximum_x = None
    lock = False

    def reset(self):
        self.latest_origin_frame = None
        self.latest_maximum_x_frame = None
        self.latest_maximum_x = None
        self.lock = False

current_objects = CurrentObjects()