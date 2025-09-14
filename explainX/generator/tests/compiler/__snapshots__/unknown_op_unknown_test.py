class Scene_Unknown_Test(Scene):
    def construct(self):
    self.wait(0.500)
    title = Text("Before Unknown", font=BODY_FONT).scale(0.9)
    self.play(Write(title))

    self.wait(0.500)
    # Unknown operation: unknown_operation
    pass

    self.wait(0.500)
    # Error generating text: generate_code() missing 3 required positional arguments: 'resolver', 'name_gen', and 'context'
    pass
