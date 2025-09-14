class Scene_Simple_Intro(Scene):
    def construct(self):
    self.wait(0.500)
    title = Text("Welcome to ExplainX", font=BODY_FONT).scale(0.9)
    self.play(Write(title))

    self.wait(0.500)
    # Error generating text: generate_code() missing 3 required positional arguments: 'resolver', 'name_gen', and 'context'
    pass

    self.wait(0.500)
    eq = MathTex(r"E = mc^2").scale(0.95)
    self.play(Write(eq))

    self.wait(1.5)
    # Pause for 1.5 seconds
    self.wait(1.5)
