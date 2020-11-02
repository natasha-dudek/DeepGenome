import random
import sys
import numpy as np
import torch

# For one rep of one genome
def heart_of_corruption_v1(org_to_mod_to_kos, org, n_max, n_kos_tot, all_kos, mod_to_ko_clean):
    """
    For each genome, keep the KO's in 1-10 modules. Everything else should be zeros
    
    Arguments:
    org (str) -- tla for genome (e.g.: "aha")
    n_max (int) -- the maximum number of mods to select for corrupted version of any given genome
    
    Returns:
    corrupted (np array) -- 
    """
    #n_mods = random.randint(1, n_max) # going to select this many mods for corrupted genome
    n_mods = 10
    keeps = random.sample(list(org_to_mod_to_kos[org].keys()), n_mods)            
    #print(org, keeps)
    idxs = []
    for mod in keeps:
        for ko in org_to_mod_to_kos[org][mod]:
        #for ko in mod_to_ko_clean[mod]:
            idxs.append(all_kos.index(ko))

    # create corrupted version of genome that only has those mods
    corrupted = np.zeros(n_kos_tot)
    for i in idxs:
        corrupted[i] = 1

    return corrupted, keeps


def heart_of_corruption_v2(org_to_mod_to_kos, org, n_max, n_kos_tot, all_kos, mod_to_ko_clean):
    """
    For each genome, remove one KO per mod (convert bits to zeros) -- how well can VAE restore a single module?
    
    Arguments:
    org (str) -- tla for genome (e.g.: "aha")
    n_max (int) -- the number of mods in a given genome
    
    Returns:
    corrupted (np array) -- 
    """
    keep_mods = list(org_to_mod_to_kos[org].keys())           

    idxs = []
    for mod in keep_mods:
        # randomly pick one KO to eliminate
        keeps = random.sample(list(org_to_mod_to_kos[org].keys()), n_mods)
    
        for ko in org_to_mod_to_kos[org][mod]:
        #for ko in mod_to_ko_clean[mod]:
            idxs.append(all_kos.index(ko))

    # create corrupted version of genome that only has those mods
    corrupted = np.zeros(n_kos_tot)
    for i in idxs:
        corrupted[i] = 1

    return corrupted, keeps

def heart_of_corruption_v3(org_to_mod_to_kos, org, n_max, n_kos_tot, all_kos, mod_to_ko_clean):
    """
    For each genome, remove  one KO from each module at random (convert bits to zeros) -- how well can VAE restore a single KO?
    
    Arguments:
    org (str) -- tla for genome (e.g.: "aha")
    n_max (int) -- the number of mods in a given genome
    
    Returns:
    corrupted (np array) -- 
    """
    keeps = random.sample(list(org_to_mod_to_kos[org].keys()), (n_max-1))            
    
    idxs = []
    for mod in org_to_mod_to_kos[org]:
        keeps = random.sample(org_to_mod_to_kos[org][mod], (len(org_to_mod_to_kos[org][mod]) - 1))
        for ko in keeps:
            idxs.append(all_kos.index(ko))
        
    # create corrupted version of genome that only has those mods
    corrupted = np.zeros(n_kos_tot)
    for i in idxs:
        corrupted[i] = 1

    return corrupted, keeps



def corrupt(train_data, train_genomes, n_corrupt, tnum_to_tla, org_to_mod_to_kos, all_kos, mod_to_ko_clean,  method):
    """
    For each genome, keep the KO's in 1-10 modules. Everything else should be zeros
    Note: creates corrupted + matching uncorrupted tensor of genomes, in that order
    Note: only genomes with >= 1 module are included in the output
    Note: uses "cleaned" modules from mod_to_ko_clean  
        I.e. most common set of KOs per module, rather than 20 variants of each mod
    
    Arguments:
    train_data (tensor) -- rows = uncorrupted genomes, columns = KOs
    train_genomes (list) -- names of genomes in train_data (e.g.: "T03060")
    n_corrupt (int) -- number of corrupted versions to make of each genome
    tnum_to_tla (dict) -- maps tnum (e.g.: "T03060") to tla (e.g.: "Red")
    method (str) -- method for performing corruption, "v1" | "v2"
    
    Returns:
    output (tensor) -- corrupted + uncorrupted genomes (each genome's two versions are concatenated in a row)
    c_train_genomes -- names of genomes in the order they appear in output
    """
        
    output = [] 
    c_train_genomes = []
    n_kos_tot = train_data.shape[1]
    input_mods = []
    
    line_counter = 0
    for i, tnum in enumerate(train_genomes):
        org = tnum_to_tla[tnum]
        n_tot_mods = len(org_to_mod_to_kos[org]) # number of modules in the genome 
        
        # needed for type v1 corruption
        n_max = min(n_tot_mods, 10) # which is smaller: the # mods or 10
        
        n_corrupted = 0
        if n_tot_mods >= 10: 
            uncorrupted = train_data[i]
            while n_corrupted < n_corrupt: 
                c_train_genomes.append(org)
                #corrupted = heart_of_corruption_v1(org_to_mod_to_kos, org, n_max, n_kos_tot, all_kos)
                if method == "v1":
                    corrupted, in_mods = heart_of_corruption_v1(org_to_mod_to_kos, org, n_max, n_kos_tot, all_kos, mod_to_ko_clean)
                elif method == "v2":
                    corrupted, in_mods = heart_of_corruption_v2(org_to_mod_to_kos, org, n_max, n_kos_tot, all_kos, mod_to_ko_clean)
                elif method == "v3":
                    corrupted, in_mods = heart_of_corruption_v3(org_to_mod_to_kos, org, n_max, n_kos_tot, all_kos, mod_to_ko_clean)
             
                genome_out = np.concatenate((corrupted, uncorrupted), axis=None)
                output.append(genome_out)
                input_mods.append(in_mods)
                line_counter += 1
                n_corrupted += 1
            
    return torch.Tensor(np.array(output)), c_train_genomes, input_mods

def corrupt_orig(data, num_corruptions, corruption_fraction):    
    """
    Stochastically drop KO's / modules from genomes
    
    Arguments:
    data (df) -- train or test dataset
    num_corruptions (int) -- number of corrupted outputs to produce per input genome
    corruption_fraction (float) -- what % of KO's/mods to drop
    
    Returns:
    out (tensor) -- training set with corrupted genomes and then uncorrupted genomes in each row
    genome_idx (dict) -- maps genome idx in corrupt_train / corrupt_test to genome ID
        E.g.: genome_idx[i] -> 'T012839'
    """
    
    num_genomes = data.shape[0] # number of genomes in the train ds
    out = np.zeros(shape=(num_genomes*num_corruptions,data.shape[1]*2))
    
    # Create dict that can trace each genome back to original genome index 
    genome_idx = {}
    genome_counter = 0
    
    print
    
    # Iterate through original genomes ---> produce corrupt versions 
    for s in range(num_genomes):
        # get indices of KO's present 
        ko_idx = np.argwhere(data[s] == 1).tolist() #[0]
        ko_idx = [item for sublist in ko_idx for item in sublist]

        uncorr_idx = [(i + data.shape[1]) for i in ko_idx]

        # generate num_corruptions corrupted genomes from original genome
        for i in range(num_corruptions):
            # random sampling of gene idxs without replacement
            keeper_idx = random.sample(ko_idx, int(len(ko_idx)*corruption_fraction))
            # retain only keeper genes
            out[genome_counter][keeper_idx] = 1
            
#            print(np.sum(out[genome_counter]))
            if np.sum(out[genome_counter]) < 1: 
                print("error", len(keeper_idx))
                print("int(len(ko_idx)*corruption_fraction)",int(len(ko_idx)*corruption_fraction))
                print("len(ko_idx)",len(ko_idx))
                raise Exception()
#                sys.exit(0)
            
            # Then add uncorrupted genome
            out[genome_counter][uncorr_idx] = 1
            genome_idx[genome_counter] = s
            genome_counter += 1
    
    out = torch.FloatTensor(out)
             
    return out, genome_idx








