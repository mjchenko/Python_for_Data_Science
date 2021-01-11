import gym
import numpy as np
import random
from keras.models import Sequential
from keras.layers import Dense, Activation
from keras.optimizers import Adam, SGD, Adadelta

#make envirnoment
env = gym.make('CartPole-v1')

#define action space and input space
act_space = env.action_space.n
input_space =env.observation_space.shape[0]

#create neural network
model = Sequential()
model.add(Dense(24, input_dim = input_space, activation = 'relu'))
model.add(Dense(24, activation = 'relu'))
model.add(Dense(act_space, activation = 'linear'))
model.add(Activation('linear'))
model.compile(loss = 'mse', optimizer = Adam())

#define hyper parameters
gamma = .95 #discount rate
eps = 1
eps_min = 0.0001
eps_decay = 0.999

#number of episodes
episodes = 5000
#number of steps
steps = 500

#creating memory for replay
mem = []
batch_size = 64
mem_max = 10000

#train the model
for episode in range(episodes):
    state = env.reset()
    state = np.array([state])

    for step in range(steps):
        # uncomment to see the render during training
        # env.render()

        # if random produced variable is less than epsilon choose random action
        if np.random.rand() <= eps:
            act = random.randint(0,1)
        else:
            #otherwise use the model to predict the action with best outcome
            act = np.argmax(model.predict(state))

        #take the action and return the next state, reward, terminal boolean, and info
        next_state, reward, done, info = env.step(act)
        next_state = np.array([next_state])

        # update q target for actions we took by taking maximum of possible outcomes
        target = reward + gamma * np.max(model.predict(next_state))
        # find q(s', a') for the actions we could have taken at original state
        target_f = model.predict(state)[0]
        #update q' with the action we took
        target_f[act] = target

        #update weights of neural network with fit
        model.fit(state, target_f.reshape(-1, act_space), epochs = 1, verbose = 0)

        #append the state, action, reward, next state, and bool to memory and move to next state
        mem.append((state, act, reward, next_state, done))
        state = next_state

        #clear room at beginning of memory if it is full
        if len(mem) == mem_max:
            del mem[:mem_max]

        #if game is done exit loop
        if done:
            print(f"Episide {episode} out of {episodes} | Score: {step}")
            break

    # decay epsilon to take less random actions as we get more episodes
    if eps > eps_min:
        eps *= eps_decay

    # memory replay
    if len(mem) > batch_size:
        minibatch = random.sample(mem, batch_size)
        for state, act, reward, next_state, done in  minibatch:
            target = reward
            if not done:
                target = reward + gamma + np.max(model.predict(next_state))

            target_f = model.predict(state)[0]
            target_f[act] = target
            model.fit(state, target_f.reshape(-1, act_space), epochs = 1, verbose = 0)


# Save weights
model.save_weights("weights.h5")
