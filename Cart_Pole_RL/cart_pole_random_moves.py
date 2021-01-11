# state[0] x position of cart
# state[1] x velocity of cart
# state[2] ang position of pole
# state[3] ang velocity of pole

# make environemt
env = gym.make('CartPole-v1')

# create new
state = env.reset()


# random action
def action_random(state):
        return random.randint(0,1)

# if ang position of pole is less than 0 move left
def action_ang_pos(state):
    if state[2] < 0:
        return 0
    else:
        return 1

def scoreboard(choose_action, episodes = 25):
    steps = 500 + 1 #we win the game if we reach 500 steps
    scores = [] #initialize empty list to store score

    # for each episode reset the environemt
    for episode in range(episodes):
        state = env.reset()

        # if the cart has not reached terminal state (500 steps)
        # or out of frame or angle of pole is more than 15 degrees off vertical
        # choose an action
        for num_steps in range(steps):
            env.render()
            action = choose_action(state)
            state_next, reward, terminal, info = env.step(action)
            state = state_next
            if terminal:
                break
        # update the scores list
        scores.append(num_steps)
    #calcualte total score as a fraction of possible
    score = sum(scores)/(steps * episodes)
    return score

print("Score based on Angular Position of Pole is: ", scoreboard(action_ang_pos))
print("Score based on Random Movement is: ", scoreboard(action_random))
