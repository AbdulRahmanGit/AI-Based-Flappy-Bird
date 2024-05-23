import pygame
import pygame.mixer
import random
import os
import time
import neat
import pickle
import sys

pygame.font.init() 
pygame.mixer.init()

WIN_WIDTH = 600
WIN_HEIGHT = 800
FLOOR = 730

# Initialize fonts
STAT_FONT = pygame.font.SysFont("opensans", 50)
END_FONT = pygame.font.SysFont("opensans", 70)

# Create game window
WIN = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
pygame.display.set_caption("AI Flappy Bird")

# Load images
pipe_img = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","pipe.png")).convert_alpha())
bg_img1 = pygame.transform.scale(pygame.image.load(os.path.join("imgs","bg.png")).convert_alpha(), (600, 900))
bird_images = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","bird" + str(x) + ".png"))) for x in range(1, 4)]
base_img = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","base.png")).convert_alpha())
bg_img2 = pygame.transform.scale(pygame.image.load(os.path.join("imgs","bg_night.jpeg")).convert_alpha(), (600, 900))

# Load sounds
flap_down_sound = pygame.mixer.Sound(os.path.join('sfx/swoosh.wav'))
collision_sound = pygame.mixer.Sound(os.path.join('sfx/hit.wav'))
flap_up_sound = pygame.mixer.Sound(os.path.join('sfx/wing.wav'))
score_sound = pygame.mixer.Sound(os.path.join('sfx/point.wav'))
bg_sound = pygame.mixer.Sound(os.path.join('sfx/bg.mp3'))
bg_sound.set_volume(0.2)
# Set global variables
gen = 0

class Bird:
    MAX_ROTATION = 25
    IMGS = bird_images
    ROT_VEL = 20
    ANIMATION_TIME = 5

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.tilt = 0
        self.tick_count = 0
        self.vel = 0
        self.height = self.y
        self.img_count = 0
        self.img = self.IMGS[0]

    def jump(self):
        self.vel = -10.5
        self.tick_count = 0
        self.height = self.y

    def move(self):
        self.tick_count += 1
        displacement = self.vel*self.tick_count + 0.5*(3)*(self.tick_count)**2

        if displacement >= 20:
            displacement = 20
        if displacement < 0:
            displacement -= 2

        self.y += displacement

        if displacement < 0 or self.y < self.height + 60:
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else:
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL
            

    def draw(self, win):
        self.img_count += 1

        if self.img_count < self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count < self.ANIMATION_TIME*2:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME*3:
            self.img = self.IMGS[2]
        elif self.img_count < self.ANIMATION_TIME*4:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME*4 + 1:
            self.img = self.IMGS[0]
            self.img_count = 0

        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME*2

        blitRotateCenter(win, self.img, (self.x, self.y), self.tilt)

    def get_mask(self):
        return pygame.mask.from_surface(self.img)

class Pipe:
    GAP = 200
    VEL = 5

    def __init__(self, x):
        self.x = x
        self.height = 0
        self.top = 0
        self.bottom = 0
        self.PIPE_TOP = pygame.transform.flip(pipe_img, False, True)
        self.PIPE_BOTTOM = pipe_img
        self.passed = False
        self.set_height()

    def set_height(self):
        self.height = random.randrange(50, 450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    def move(self, speed_multiplier):
        self.x -= self.VEL * speed_multiplier

    def draw(self, win):
        win.blit(self.PIPE_TOP, (self.x, self.top))
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    def collide(self, bird):
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)
        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))
        b_point = bird_mask.overlap(bottom_mask, bottom_offset)
        t_point = bird_mask.overlap(top_mask, top_offset)

        if t_point or b_point:
            collision_sound.play()
            return True
        return False

class Base:
    VEL = 6
    WIDTH = base_img.get_width()
    IMG = base_img

    def __init__(self, y):
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self, speed_multiplier):
        self.x1 -= self.VEL * speed_multiplier
        self.x2 -= self.VEL * speed_multiplier

        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH

        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self, win):
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))

def blitRotateCenter(surf, image, topleft, angle):
    rotated_image = pygame.transform.rotate(image, angle)
    new_rect = rotated_image.get_rect(center=image.get_rect(topleft=topleft).center)
    surf.blit(rotated_image, new_rect.topleft)

def draw_window(win, birds, pipes, base, score, gen, pipe_ind, bg_img):
    if gen == 0:
        gen = 1
    win.blit(bg_img, (0, 0))

    for pipe in pipes:
        pipe.draw(win)

    base.draw(win)
    for bird in birds:
        bird.draw(win)

    score_label = STAT_FONT.render("Score: " + str(score), 1, (255, 255, 255))
    win.blit(score_label, (WIN_WIDTH - score_label.get_width() - 15, 10))

    score_label = STAT_FONT.render("Gens: " + str(gen-1), 1, (255, 255, 255))
    win.blit(score_label, (10, 10))

    score_label = STAT_FONT.render("Alive: " + str(len(birds)), 1, (255, 255, 255))
    win.blit(score_label, (10, 50))

    pygame.display.update()

def eval_genomes(genomes, config):
    global WIN, gen, bg_img1, bg_img2
    win = WIN
    gen += 1
    speed_multiplier = 1 
    nets = []
    birds = []
    ge = []

    for genome_id, genome in genomes:
        genome.fitness = 0
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        nets.append(net)
        birds.append(Bird(230, 350))
        ge.append(genome)

    base = Base(FLOOR)
    pipes = [Pipe(700)]
    score = 0

    clock = pygame.time.Clock()
    bg_img = bg_img1
    run = True
    target_score = 100
    transition_duration = 100
    transition_alpha = 0.5
    transitioning = False

    bg_sound.play(loops=-1)
    while run and len(birds) > 0:
        clock.tick(40)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()
            keys = pygame.key.get_pressed()
            if keys[pygame.K_j]:
                for bird in birds:
                    bird.jump()

        speed_multiplier = 1 + (score / 30)

        
        # Check if transition should occur
        if score >= 40 and score < 70:
            transitioning = True
        else:
            transitioning = False

        # Smooth transition logic
        if transitioning:
            transition_alpha += 255 / transition_duration
            if transition_alpha >= 255:
                transition_alpha = 255
        else:
            transition_alpha -= 255 / transition_duration
            if transition_alpha <= 0:
                transition_alpha = 0

        # Switch background based on score
        if score >= 40 and score < 70:
            bg_img = bg_img2
        else:
            bg_img = bg_img1

        # Blit both backgrounds with smooth transition
        win.blit(bg_img1, (0, 0))
        bg_img2.set_alpha(int(transition_alpha))
        win.blit(bg_img2, (0, 0))

        pipe_ind = 0
        if len(birds) > 0:
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                pipe_ind = 1

        for x, bird in enumerate(birds):
            bird.move()
            ge[x].fitness += 0.1

            output = nets[x].activate((bird.y, abs(bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom)))

            if output[0] > 0.5:
                bird.jump()
                

        add_pipe = False
        rem = []
        for pipe in pipes:
            pipe.move(speed_multiplier)
            for bird in birds:
                if pipe.collide(bird):
                    ge[birds.index(bird)].fitness -= 1
                    idx = birds.index(bird)
                    birds.pop(idx)
                    nets.pop(idx)
                    ge.pop(idx)

            if not pipe.passed and pipe.x < bird.x:
                pipe.passed = True
                add_pipe = True

            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)

        if add_pipe:
            score += 1
            score_sound.play()
            for g in ge:
                g.fitness += 5
            pipes.append(Pipe(WIN_WIDTH))

        for r in rem:
            pipes.remove(r)

        for bird in birds:
            if bird.y + bird.img.get_height() >= 730 or bird.y < 0:
                idx = birds.index(bird)
                birds.pop(idx)
                nets.pop(idx)
                ge.pop(idx)

        base.move(speed_multiplier)
        draw_window(win, birds, pipes, base, score, gen, pipe_ind, bg_img)
        if score >= target_score:
            pickle.dump(nets[0],open("best.pickle", "wb"))
            print("Reached target score! Exiting the game.")
            break

def run(config_file):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet, neat.DefaultStagnation, config_file)
    p = neat.Population(config)
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    p.add_reporter(neat.Checkpointer(5))

    winner = p.run(eval_genomes, 50)
    with open("best.pickle", "wb") as f:
        pickle.dump(winner, f)

if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "config-feedforward.txt")
    run(config_path)
























