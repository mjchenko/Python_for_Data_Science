import gym
import numpy as np
import random
from keras.models import Sequential
from keras.layers import Dense, Activation
from keras.optimizers import Adam, SGD, Adadelta
from time import sleep

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

# Load weights generated from training.py
model.load_weights("weights.h5")

# Play game
print("-----------------------------")
print("Play CartPole")
print("-----------------------------")

score = 0
state = env.reset()
done = False
while not done:
    env.render()
    sleep(0.1)
    act = np.argmax(model.predict(np.array([state])))
    next_state, reward, done, info = env.step(act)
    state = next_state
    score += 1

print(f"your score was: {score}")
