import random
import math
import multiprocessing
import numpy

# Generalized Beam Search: Based on parameters (see run function), can run GA, SA, HC, or a hybrid of these strategies.
class GeneralizedBeamSearch:
    def cross(self, p1, p2, idx):
        return p1[:idx] + p2[idx:]

    def mutate(self, gen, mutationChance, alwaysChange):
        numMutated = min(numpy.random.poisson(len(gen) * mutationChance) + alwaysChange, len(gen))
        newGen = gen.copy()
        for pos in random.sample(range(len(gen)), numMutated):
            newGen[pos] = self.mutate1(newGen[pos])
        return (alwaysChange, newGen)

    def breed(self, p1, p2, pMut):
        crossoverIdx = random.randrange(0, len(p1))
        (c1, c2) = tuple([self.mutate(self.cross(a, b, crossoverIdx), pMut, mustMutate) for (a, b, mustMutate) in [(p1, p2, True), (p2, p1, False)]])
        return (c1, c2)

    def sortGeneration(self, pop, T):
        best = sorted(pop, key=lambda s: s[0], reverse=True)
        if (T == 0):
            return best
        nextBestPos = (len(pop)-1)//2
        nextBestFitness = best[nextBestPos][0]
        for i in range(len(pop)//2):
            (fitness, fresh, gen) = best[i]
            if (not fresh):
                fitnessDiff = fitness - nextBestFitness
                pKill = math.exp(- fitnessDiff / T)
                if (random.random() < pKill):
                    nextBestPos += 1
                    nextBestFitness = best[nextBestPos][0]
                else:
                    best[i] = (fitness, True, gen)
        return sorted(best, key=lambda s: s[0] if s[1] else -1, reverse=True)

    def newGeneration(self, scored, pMut, breedingPortion, mutatingPortion):
        numPairs = int(len(scored)*breedingPortion)
        toBreed = numPairs * 2
        toMutate = int(len(scored)*mutatingPortion)
        toKeep = len(scored) - toBreed - toMutate
        breeders = [ gen for (fitness, fresh, gen) in scored[:toBreed]]
        random.shuffle(breeders)
        pairs = zip(breeders[:numPairs], breeders[numPairs:])
        # Might want to pull score out of breed to simplify parallelization
        children = [ child for (p1, p2) in pairs for child in self.breed(p1, p2, pMut)]
        mutated = [ (self.mutate(gen, pMut, True)) for (fitness, fresh, gen) in scored[:toMutate] ]
   
        #children + mutated need to be scored
        #concatenate the two lists
        unscored = children + mutated
        scored = [self.score(mut)for mut in unscored]
        keepers = [ (fitness, False, gen) for (fitness, fresh, gen) in scored[:toKeep] ]
        return keepers + scored
#        return keepers + mutated + children

    # Temperature Schedule (for SA): Defines odds of exploring a worse solution over time. Set to always 0 for non-SA
    # Mutation Schedule: Defines odds of mutating an individual gene, over time
    # Breeding portion: Defines number of breeding pairs per generation. Eg portion=1/3 means 2/3 of the populatin will be included in a breeding pair. Set to 0 for SA or HC.
    # Mutating portion: Defines portion of population to mutate (without breeding) each generation. Set to 0 for pure GA.
    def run(self, population, temperatureSchedule, mutationSchedule, breedingPortion, mutatingPortion, iterations, printProgress):
        printed = 0
        for i in range(iterations):
            T = temperatureSchedule(i, iterations)
            pMut = mutationSchedule(i, iterations)
            scored = self.sortGeneration(population, T)
            if (printProgress and pow(1.5, printed - 7) + printed*printed / 12 + printed * 2 - 3 <= i):
                printed += 1
                scores = [ score for (score, fresh, gen) in scored[:10] ]
                print(f"Generation {i}: {scores}")
                if (len(scored[0][2]) < 50):
                    print(scored[0][2])
            population = self.newGeneration(scored, pMut, breedingPortion, mutatingPortion)
        scored = self.sortGeneration(population, 0)
        if (printProgress):
            print("Value:", scored[0][0])
            self.printInfo(scored[0][2])
            print(scored[0][2])
        return scored[0][0]

    def printInfo(self, gen): pass

# Stuff specific to Knapsack Problem. Should be removed later, but useful as code template
class KittensProblem(GeneralizedBeamSearch):
    def __init__(self, buildings, build_order_length):
        self.buildings = buildings
        self.build_order_length = build_order_length

    # score is the function that should send the genome to another computer to be tested for fitness in Simba
    # we might want to keep a cache of recently-scored genomes, and use the cached result if we have duplicate genomes in the population, since scoring is extremely expensive
    def score(self, mut):
        (fresh, gen) = mut
        return (self.fitness_function(gen), fresh, gen)

    # TODO: this should simulate the game and compute a score. The current implementation is a stub for testing.
    def fitness_function(self, gen):
        fitness = 0
        if gen[0] == "Field":
            fitness += 1
        if gen[1] == "Hut":
            fitness += 1
        if gen[2] == "Barn":
            fitness += 1
        if gen[3] == "Library":
            fitness += 1
        return fitness

    #princess kim's implementation of mutate
    def mutate(self, genome, mutationChance, alwaysChange):
        #TODO: make it so that adding has a lower probability than removing?
        #a random number of buildings to add
        numAdded = min(numpy.random.poisson(len(genome) * mutationChance) + alwaysChange, len(genome))
        #a random number of buildings to remove
        numRemoved = min(numpy.random.poisson(len(genome) * mutationChance) + alwaysChange, len(genome))
        newGenome = genome.copy()
        for x in range (numRemoved):    #loop numRemoved times
            pos = random.randrange(len(newGenome)) 
            del newGenome[pos]    
#        for pos in random.sample(range(len(NewGenome)), numRemoved):      #removes a building from a random position
#            del newGenome[pos]

        for pos in random.sample(range(len(newGenome)), numAdded):        #inserts a random building at random positions
            newGenome.insert(pos, random.choice(self.buildings))
        return (alwaysChange, newGenome)

    def printInfo(self, gen):
        print(",".join(gen[0:min(10, len(gen))]))

    def randomGenome(self):
#        gen = random.choices(self.buildings, k=self.build_order_length) #Returns a list of k-size elements
        gen = [] 
        for pos in range(self.build_order_length):
            gen.append(random.choice(self.buildings))
#        return self.score((True, gen)) #Returns the score that corresponds to that list of elements
        return gen      #returns UNSCORED genome?


#example parameters
def temperatureSchedule2(t, iterations):
    #return max((1 - t / iterations * 1.2) * 10000, 0)
    return pow(.98, (t)) * 10000 * max((1 - t / iterations * 1.2), 0)
def temperatureSchedule0(t, iterations):
    return 0
def mutationSchedule(t, iterations):
    #return (1 - t / iterations) * 0.002
    #return T * .002
    return 0.004

#define and run different problems
def kittensTrial(j):
    buildings = [
        "Field",
        "Hut",
        "Barn",
        "Pasture",
        "Library",
        "Mine"
    ]

#   build order length is used to initialize the genomes size at first. 
#   size is not fixed, genomes can shrink or grow depending on how it is mutated    
#   buildings can be bought (and should be bought) multiple times, so the build length is a multiple of the number of buildings
    build_order_length = len(buildings) * 3
    kittensProblem = KittensProblem(buildings, build_order_length)
    populationSize = 800
    #score population? 
    unscored_population = [ kittensProblem.randomGenome() for i in range(populationSize) ]
    population = [kittensProblem.score((True, gen)) for gen in unscored_population]
    return kittensProblem.run(population, temperatureSchedule0, mutationSchedule, 1/3, 0/2, 10, j == 0)

if __name__ == "__main__":
    kittensTrial(0)
