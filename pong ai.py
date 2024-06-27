import pygame
import math 
import random
import neat
import os
import pickle
pygame.init()

# Font that is used to render the text
font20 = pygame.font.Font('freesansbold.ttf', 20)

# RGB values of standard colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)

# Basic parameters of the screen
WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pong")

clock = pygame.time.Clock() 


# Striker class


class Striker:
        # Take the initial position, dimensions, speed and color of the object
    def __init__(self, posx, posy, width, height, speed, color):
        self.posx = posx
        self.posy = posy
        self.width = width
        self.height = height
        self.speed = speed
        self.color = color
        # Rect that is used to control the position and collision of the object
        self.playerRect = pygame.Rect(posx, posy, width, height)
        # Object that is blit on the screen
        self.player = pygame.draw.rect(screen, self.color, self.playerRect)
        self.hit=0

    # Used to display the object on the screen
    def display(self):
        self.player = pygame.draw.rect(screen, self.color, self.playerRect)

    def update(self, yFac):
        self.posy = self.posy + self.speed*yFac

        # Restricting the striker to be below the top surface of the screen
        if self.posy <= 0:
            self.posy = 0
        # Restricting the striker to be above the bottom surface of the screen
        elif self.posy + self.height >= HEIGHT:
            self.posy = HEIGHT-self.height

        # Updating the rect with the new values
        self.playerRect = (self.posx, self.posy, self.width, self.height)

    def displayScore(self, text, score, x, y, color):
        text = font20.render(text+str(score), True, color)
        textRect = text.get_rect()
        textRect.center = (x, y)

        screen.blit(text, textRect)

    def getRect(self):
        return self.playerRect

# Ball class


class Ball:
    def __init__(self, posx, posy, radius, speed, color):
        self.posx = posx
        self.posy = posy
        self.radius = radius
        self.speed = speed
        self.color = color
        self.xFac = 1
        self.yFac = -1
        self.ball = pygame.draw.circle(
            screen, self.color, (self.posx, self.posy), self.radius)
        self.firstTime = 1
        angle = self._get_random_angle(-30, 30, [0])
        pos = 1 if random.random() < 0.5 else -1
        self.x_vel = pos * abs(math.cos(angle) * self.speed)
        self.y_vel = math.sin(angle) * self.speed

    def display(self):
        self.ball = pygame.draw.circle(
            screen, self.color, (self.posx, self.posy), self.radius)
        
    def _get_random_angle(self, min_angle, max_angle, excluded):
        angle = 0
        while angle in excluded:
            angle = math.radians(random.randrange(min_angle, max_angle))
        return angle
    
    def update(self):
        self.posx += self.x_vel*self.xFac
        self.posy += self.y_vel*self.yFac

        # If the ball hits the top or bottom surfaces, 
        # then the sign of yFac is changed and 
        # it results in a reflection
        if self.posy <= 0 or self.posy >= HEIGHT:
            self.yFac *= -1

        if self.posx <= 0 and self.firstTime:
            self.firstTime = 0
            return 1
        elif self.posx >= WIDTH and self.firstTime:
            self.firstTime = 0
            return -1
        else:
            return 0

    def reset(self):
        self.posx = WIDTH//2
        self.posy = HEIGHT//2

        angle = self._get_random_angle(-30, 30, [0])
        x_vel = abs(math.cos(angle) * self.speed)
        y_vel = math.sin(angle) * self.speed

        self.y_vel = y_vel
        self.x_vel *= -1
        self.xFac *= -1
        self.firstTime = 1

    # Used to reflect the ball along the X-axis
    def hit(self):
        self.xFac *= -1

    def getRect(self):
        return self.ball

# Game Manager
def display_totalhits(player1,player2):
    total_hits=player1.hit+player2.hit
    text = font20.render("HITS="+str(total_hits), True, WHITE)
    textRect = text.get_rect()
    textRect.center = (WIDTH/2, 50)

    screen.blit(text, textRect)


def play_ai(winner_net):
    running = True
    FPS=60
    # Defining the objects
    player1 = Striker(20, HEIGHT/2+10, 10, 100, 10, GREEN)
    player2 = Striker(WIDTH-30, HEIGHT/2+10, 10, 100, 10, GREEN)
    ball = Ball(WIDTH//2, HEIGHT//2, 7, 7, WHITE)

    listOfplayers = [player1, player2]

    # Initial parameters of the players
    player1Score, player2Score = 0, 0
    player1YFac, player2YFac = 0, 0

    while running:
        screen.fill(BLACK)

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    player2YFac = -1
                if event.key == pygame.K_DOWN:
                    player2YFac = 1
                
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_UP or event.key == pygame.K_DOWN:
                    player2YFac = 0
                

        # Collision detection
        for player in listOfplayers:
            if pygame.Rect.colliderect(ball.getRect(), player.getRect()):
                ball.hit()

        # Updating the objects
        player1.update(player1YFac)
        player2.update(player2YFac)
        point = ball.update()

        # -1 -> player_1 has scored
        # +1 -> player_2 has scored
        # 0 -> None of them scored
        if point == -1:
            player1Score += 1
        elif point == 1:
            player2Score += 1

        output1=winner_net.activate((player1.posy,abs(ball.posx-player1.posx),ball.posy))
        decision1=output1.index(max(output1))
        
        if decision1==1:
            player1YFac=-1
        elif decision1==2:
            player1YFac=1
        # Someone has scored
        # a point and the ball is out of bounds.
        # So, we reset it's position
        if point: 
            ball.reset()

        # Displaying the objects on the screen
        player1.display()
        player2.display()
        ball.display()

        # Displaying the scores of the players
        player1.displayScore("player_1 : ", 
                        player1Score, 100, 15, WHITE)
        player2.displayScore("player_2 : ", 
                        player2Score, WIDTH-100, 15, WHITE)

        pygame.display.update()
        clock.tick(FPS)	 


def play_genomes(genome1,genome2,config):

    net1=neat.nn.FeedForwardNetwork.create(genome1,config)
    net2=neat.nn.FeedForwardNetwork.create(genome2,config)
    FPS=2400
    
    
    running = True

    # Defining the objects
    player1 = Striker(20, HEIGHT/2+10, 10, 100, 10, GREEN)
    player2 = Striker(WIDTH-30, HEIGHT/2+10, 10, 100, 10, GREEN)
    ball = Ball(WIDTH//2, HEIGHT//2, 7, 7, WHITE)

    listOfplayers = [player1, player2]

    # Initial parameters of the players
    player1Score, player2Score = 0, 0
    player1YFac, player2YFac = 0, 0
    player1.hit,player2.hit=0,0
    while running:
        screen.fill(BLACK)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
        
        for player in listOfplayers:
            if pygame.Rect.colliderect(ball.getRect(), player.getRect()):
                ball.hit()
                player.hit+=1
        
        output1=net1.activate((player1.posy,abs(ball.posx-player1.posx),ball.posy))
        decision1=output1.index(max(output1))
        
        if decision1==1:
            player1YFac=-1
        elif decision1==2:
            player1YFac=1

        output2=net2.activate((player2.posy,abs(ball.posx-player2.posx),ball.posy))
        decision2=output2.index(max(output2))

        if decision2==1:
            player2YFac=-1
        elif decision2==2:
            player2YFac=1
        
        # Updating the objects
        player1.update(player1YFac)
        player2.update(player2YFac)
        point = ball.update()

        #1 -> player_1 has scored
        # +1 -> player_2 has scored
        # 0 -> None of them scored
        if point == -1:
            player1Score += 1
        elif point == 1:
            player2Score += 1

        # Someone has scored
        # a point and the ball is out of bounds.
        # So, we reset it's position
        if point: 
            ball.reset()

        # Displaying the objects on the screen
        player1.display()
        player2.display()
        ball.display()

        # Displaying the scores of the players
        #player1.displayScore("player_1 : ", 
         #               player1Score, 100, 20, WHITE)
        
        #player2.displayScore("player_2 : ", 
          #             player2Score, WIDTH-100, 20, WHITE)
        
        display_totalhits(player1,player2)
        
        pygame.display.update()
        

        
        if player1Score>=1 or player2Score>=1 or player1.hit>=50:
            genome1.fitness+=player1.hit
            genome2.fitness+=player2.hit 
            
            break
        clock.tick(FPS)




def eval_genomes(genomes,config):
    
    for i,(genome_id1,genome1) in enumerate(genomes):
        genome1.fitness=0.0
        if i+1== len(genomes):
             break
        for genome_id2,genome2 in genomes[i+1:]:
            if genome2.fitness==None: 
                genome2.fitness=0
            play_genomes(genome1,genome2,config)
            

        



def run_neat(config):
    p = neat.Population(config)
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    p.add_reporter(neat.Checkpointer(1))	
    winner=p.run(eval_genomes,75)
    with open("best.pickle", "wb") as f:
        pickle.dump(winner, f)

def test_best_network(config):
    with open("best.pickle", "rb") as f:
        winner = pickle.load(f)
    winner_net = neat.nn.FeedForwardNetwork.create(winner, config)
    play_ai(winner_net)



if __name__ == "__main__":
    
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'configuration.ini')
    

    config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation,
                         config_path)
    run_neat(config)
    test_best_network(config)