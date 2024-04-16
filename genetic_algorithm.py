import pickle
import random
import time
from typing import List
import numpy as np
import threading
from individual import Individual
from config import *


def init_population() -> List[Individual]:
    population = [Individual(INPUT_SIZE, HIDDEN_LAYERS_NUM, HIDDEN_LAYERS_NEURONS) for _ in range(POPULATION_SIZE)]
    return population


def fitness_eval(population: List[Individual]) -> List[float]:
    fitness_values = []
    for individual in population:
        # fitness = individual.score * 50 + individual.time_alive - (
        #         10 * len(individual.moves) / len(individual.unique_moves)
        # )
        # fitness = individual.score * 500 + individual.bonus_fitness
        # for move_frequency in individual.move_frequency.values():
        #     if move_frequency / len(individual.move_frequency.values()) > 0.33:
        #         fitness -= 50
        fitness = 2 ** (individual.score + 1) + individual.bonus_fitness + individual.time_alive / 100
        fitness_values.append(fitness)
    return fitness_values


# def select_parents(population: List[Individual], fitness_values: List[int]) -> List[Individual]:
#     combined = list(zip(population, fitness_values))
#     sorted_combined = sorted(combined, key=lambda x: x[1], reverse=True)
#     selected_parents = [sorted_combined[0][0], sorted_combined[1][0]]
#     return selected_parents


def select_new_population(population, fitness_scores):
    sorted_indices = np.argsort(fitness_scores)[::-1]
    selected_parents_indices = sorted_indices[:POPULATION_SIZE // 2]
    parents = [population[i] for i in selected_parents_indices]

    children = []
    mutated_number = 0

    while len(children) < POPULATION_SIZE:
        parent1 = np.random.choice(parents)
        parent2 = np.random.choice(parents)
        if random.random() < CROSSOVER_TYPE_RATE:
            child = uniform_crossover(parent1, parent2)
        else:
            child = single_point_crossover(parent1, parent2)
        if random.random() < MUTATION_PROB:
            mutated_number += 1
            child = mutate(child)
        children.append(child)

    return children, mutated_number


def single_point_crossover(parent1, parent2):
    offspring = Individual(
        parent1.layers[0].shape[1],
        len(parent1.layers) - 1,
        parent1.layers[-1].shape[1],
        is_copy=True
    )

    for layer1, layer2 in zip(parent1.layers, parent2.layers):
        crossover_point = np.random.randint(0, len(layer1.ravel()))
        offspring_layer = np.concatenate((layer1.ravel()[:crossover_point],
                                          layer2.ravel()[crossover_point:]))
        offspring.layers.append(offspring_layer.reshape(layer1.shape))

    for bias1, bias2 in zip(parent1.biases, parent2.biases):
        crossover_point = np.random.randint(0, len(bias1.ravel()))
        offspring_bias = np.concatenate((bias1.ravel()[:crossover_point],
                                         bias2.ravel()[crossover_point:]))
        offspring.biases.append(offspring_bias.reshape(-1, 1))

    crossover_point = np.random.randint(0, len(parent1.outputs.ravel()))
    offspring_outputs = np.concatenate((parent1.outputs.ravel()[:crossover_point],
                                        parent2.outputs.ravel()[crossover_point:]))
    offspring.outputs = offspring_outputs.reshape(parent1.outputs.shape)

    return offspring


# def select_one_of_best(population: List[Individual], fitness_values: List[int]) -> Individual:
#     combined = list(zip(population, fitness_values))
#     sorted_combined = sorted(combined, key=lambda x: x[1], reverse=True)
#     return random.choice(sorted_combined[:int(POPULATION_SIZE * 0.1)])[0]


def uniform_crossover(parent1: Individual, parent2: Individual) -> Individual:
    offspring = Individual(
        parent1.layers[0].shape[1],
        len(parent1.layers) - 1,
        parent1.layers[-1].shape[1],
        is_copy=True
    )

    for layer1, layer2 in zip(parent1.layers, parent2.layers):
        random_crossover_probs = np.random.rand(*layer1.shape)
        mask = random_crossover_probs < CROSSOVER_RATE
        offspring_layer = np.where(mask, layer2, layer1)
        offspring.layers.append(offspring_layer)

    for bias1, bias2 in zip(parent1.biases, parent2.biases):
        random_crossover_probs = np.random.rand(*bias1.shape)
        mask = random_crossover_probs < CROSSOVER_RATE
        offspring_bias = np.where(mask, bias2, bias1)
        offspring.biases.append(offspring_bias)

    random_crossover_probs = np.random.rand(*parent1.outputs.shape)
    mask = random_crossover_probs < CROSSOVER_RATE
    offspring.outputs = np.where(mask, parent2.outputs, parent1.outputs)

    return offspring


def mutate(individual: Individual) -> Individual:
    mutated_individual = Individual(
        individual.layers[0].shape[1],
        len(individual.layers) - 1,
        individual.layers[-1].shape[1],
        is_copy=True
    )

    for layer in individual.layers:
        random_mutation_probs = np.random.rand(layer.shape[0], layer.shape[1])

        random_mutation_probs = np.where(random_mutation_probs < MUTATION_PROB,
                                         np.random.normal(0, 1, size=random_mutation_probs.shape) / 5,
                                         0)
        new_layer = layer + random_mutation_probs
        # mutated_values_mask = (random_mutation_probs != 0)
        # new_layer[mutated_values_mask] = np.clip(new_layer[mutated_values_mask], -1, 1)
        mutated_individual.layers.append(new_layer)

    for bias in individual.biases:
        random_mutation_probs = np.random.rand(bias.shape[0], 1)
        random_mutation_probs = np.where(random_mutation_probs < MUTATION_PROB,
                                         np.random.normal(0, 1, size=random_mutation_probs.shape) / 5,
                                         0)
        new_bias = bias + random_mutation_probs
        # mutated_values_mask = (random_mutation_probs != 0)
        # new_bias[mutated_values_mask] = np.clip(new_bias[mutated_values_mask], -1, 1)
        mutated_individual.biases.append(new_bias)

    random_mutation_probs = np.random.rand(individual.outputs.shape[0], individual.outputs.shape[1])
    random_mutation_probs = np.where(random_mutation_probs < MUTATION_PROB,
                                     np.random.normal(0, 1, size=random_mutation_probs.shape) / 5,
                                     0)
    new_layer = individual.outputs + random_mutation_probs
    # mutated_values_mask = (random_mutation_probs != 0)
    # new_layer[mutated_values_mask] = np.clip(new_layer[mutated_values_mask], -1, 1)
    mutated_individual.outputs = new_layer
    return mutated_individual


# def crossover(parent1: Individual, parent2: Individual) -> List[Individual]:
#     population = []
#     for _ in range(POPULATION_SIZE):
#         offspring = Individual(
#             parent1.layers[0].shape[1],
#             len(parent1.layers) - 1,
#             parent1.layers[-1].shape[1],
#             is_copy=True
#         )
#
#         for layer1, layer2 in zip(parent1.layers, parent2.layers):
#             random_crossover_probs = np.random.rand(layer1.shape[0], layer1.shape[1])
#             random_crossover_probs = np.where(random_crossover_probs < CROSSOVER_RATE, 1, 0)
#             mask = random_crossover_probs == 1
#             layer1[mask] = layer2[mask]
#             offspring.layers.append(layer1)
#
#         for bias1, bias2 in zip(parent1.biases, parent2.biases):
#             random_crossover_probs = np.random.rand(bias1.shape[0], 1)
#             random_crossover_probs = np.where(random_crossover_probs < CROSSOVER_RATE, 1, 0)
#             mask = random_crossover_probs == 1
#             bias1[mask] = bias2[mask]
#             offspring.biases.append(bias1)
#
#         random_crossover_probs = np.random.rand(parent1.outputs.shape[0], parent1.outputs.shape[1])
#         random_crossover_probs = np.where(random_crossover_probs < CROSSOVER_RATE, 1, 0)
#         mask = random_crossover_probs == 1
#         parent1.outputs[mask] = parent2.outputs[mask]
#         offspring.outputs = parent1.outputs
#         population.append(offspring)
#     return population


# def mutate(population: List[Individual]) -> [List[Individual], int]:
#     population_copy = population[:]
#     mutated_number = 0
#     for i in range(len(population_copy)):
#         if random.random() < MUTATION_PROB:
#             mutated_number += 1
#             individual = population_copy[i]
#             mutated_individual = Individual(
#                 individual.layers[0].shape[1],
#                 len(individual.layers) - 1,
#                 individual.layers[-1].shape[1],
#                 is_copy=True
#             )
#
#             for layer in individual.layers:
#                 random_mutation_probs = np.random.rand(layer.shape[0], layer.shape[1])
#
#                 random_mutation_probs = np.where(random_mutation_probs < MUTATION_PROB,
#                                                  np.random.normal(0, 1, size=random_mutation_probs.shape) / 5,
#                                                  0)
#                 new_layer = layer + random_mutation_probs
#                 # mutated_values_mask = (random_mutation_probs != 0)
#                 # new_layer[mutated_values_mask] = np.clip(new_layer[mutated_values_mask], -1, 1)
#                 mutated_individual.layers.append(new_layer)
#
#             for bias in individual.biases:
#                 random_mutation_probs = np.random.rand(bias.shape[0], 1)
#                 random_mutation_probs = np.where(random_mutation_probs < MUTATION_PROB,
#                                                  np.random.normal(0, 1, size=random_mutation_probs.shape) / 5,
#                                                  0)
#                 new_bias = bias + random_mutation_probs
#                 # mutated_values_mask = (random_mutation_probs != 0)
#                 # new_bias[mutated_values_mask] = np.clip(new_bias[mutated_values_mask], -1, 1)
#                 mutated_individual.biases.append(new_bias)
#
#             random_mutation_probs = np.random.rand(individual.outputs.shape[0], individual.outputs.shape[1])
#             random_mutation_probs = np.where(random_mutation_probs < MUTATION_PROB,
#                                              np.random.normal(0, 1, size=random_mutation_probs.shape) / 5,
#                                              0)
#             new_layer = individual.outputs + random_mutation_probs
#             # mutated_values_mask = (random_mutation_probs != 0)
#             # new_layer[mutated_values_mask] = np.clip(new_layer[mutated_values_mask], -1, 1)
#             mutated_individual.outputs = new_layer
#
#             population_copy[i] = mutated_individual
#     return population_copy, mutated_number


def save_individual(snake: Individual, filename):
    with open(f"{filename}.obj", 'wb') as file_save:
        to_save = {"layers": snake.layers,
                   "biases": snake.biases,
                   "outputs": snake.outputs}
        pickle.dump(to_save, file_save, protocol=pickle.HIGHEST_PROTOCOL)


def load_individual(filename):
    with open(filename, 'rb') as file_save:
        snake_params = pickle.load(file_save)

        snake = Individual(INPUT_SIZE, HIDDEN_LAYERS_NUM, HIDDEN_LAYERS_NEURONS, True)
        snake.layers = snake_params["layers"]
        snake.biases = snake_params["biases"]
        snake.outputs = snake_params["outputs"]

        return snake


def save_population(population: list, filename):
    with open(f"{filename}.obj", 'wb') as file_save:
        pickle.dump(len(population), file_save)
        for snake in population:
            to_save = {"layers": snake.layers,
                       "biases": snake.biases,
                       "outputs": snake.outputs}
            pickle.dump(to_save, file_save, protocol=pickle.HIGHEST_PROTOCOL)


def load_population(filename):
    population = []
    with open(f"{filename}.obj", 'rb') as file_save:
        num_population = pickle.load(file_save)
        for _ in range(num_population):
            snake_params = pickle.load(file_save)
            snake = Individual(INPUT_SIZE, HIDDEN_LAYERS_NUM, HIDDEN_LAYERS_NEURONS, True)
            snake.layers = snake_params["layers"]
            snake.biases = snake_params["biases"]
            snake.outputs = snake_params["outputs"]
            population.append(snake)
    return population

# ind1, ind2 = Individual(INPUT_SIZE, HIDDEN_LAYERS_NUM, HIDDEN_LAYERS_NEURONS), Individual(INPUT_SIZE, HIDDEN_LAYERS_NUM,
#                                                                                           HIDDEN_LAYERS_NEURONS)
# child = single_point_crossover(ind1, ind2)
#
# for layer, p_l1, p_l2 in zip(child.layers, ind1.layers,
#                              ind2.layers):
#     print(layer == p_l1)
#     print("next")
#     print(layer == p_l2)
#     print("*" * 15)
#
# for layer, p_l1, p_l2 in zip(child.biases, ind1.biases,
#                              ind2.biases):
#     print(layer == p_l1)
#     print("next")
#     print(layer == p_l2)
#     print("*" * 15)
#
# print("*" * 15)
# print(child.outputs == ind1.outputs)
# print("next")
# print(child.outputs == ind2.outputs)