class Scene_Img_Demo(Scene):
    def construct(self):
    self.wait(0.500)
    title = Text("Image Integration Demo", font=BODY_FONT).scale(0.9).to_edge(UP)
    self.play(Write(title))

    self.wait(0.500)
    img = ImageMobject("/assets/test/demo_image.png").scale_to_fit_width(6.0)
    self.play(FadeIn(img))

    self.wait(0.500)
    # Error generating text: generate_code() missing 3 required positional arguments: 'resolver', 'name_gen', and 'context'
    pass

    self.wait(3.0)
    # Pause for 3.0 seconds
    self.wait(3.0)
