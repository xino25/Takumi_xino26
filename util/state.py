class State:
    def __init__(self):
        self.done = False
        self.quit = False
        self.next_state = None

    def handle_events(self, events):
        pass

    def update(self, dt):
        pass

    def draw(self, screen):
        pass