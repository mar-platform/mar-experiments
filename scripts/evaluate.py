import argparse
import json
import os

import numpy as np
import requests
import pandas as pd


class MARSearch:
    def getScores(self, datain):
        url = "http://localhost:8080/search/example?type=ecore&syntax=xmi"
        r = requests.post(url, data=datain)
        response = json.loads(r.content.decode('utf-8'))
        return response


class MAREvaluation:
    def __init__(self):
        self.search = MARSearch()

    def getScoresFile(self, doc):
        with open(doc, 'r') as file:
            data = file.read()
            scores = self.search.getScores(data)
            scores = scores[0:100]
            # Get the last 3 parts of the id as representative
            return [(s['name'], self.get_comparable_id(s['id'])) for s in scores]

    def get_comparable_id(self, id):
        return "/".join(id.split('/')[-3:])

    def position2(self, scores, doc):
        doc_id = self.get_comparable_id(doc)
        #print("DocId: ", doc_id)
        #print("Scores: ", scores)
        for i, (name, id) in enumerate(scores):
            if id == doc_id:
                #print("Match: ", i, id, doc_id)
                #print("---")
                return i + 1
        print("Cannot find: ", doc)
        return None
        #print("----")

#        names = list(scores)
#        i = 1
#        last_score = scores[names[0]]
#        if names[0] == doc:
#            return i
#        for n in names[1:]:
#            i = i + 1
#            last_score = scores[n]
#            if (n == doc):
#                return i
#        return None

    def search_mutations(self, original, mutations):
        """
        Given the path of the original models and a list of mutations derived from it (in the form of paths),
        return the mean reciprocal rank of the mutations with respect to the original model.
        """
        positions = []
        ps = []
        rr = []
        for file in mutations:
            scores = self.getScoresFile(file)
            if len(scores) == 0:
                positions.append(0)
                rr.append(0)
                ps.append('>100')
                continue

            p = self.position2(scores, original)

            if p:
                positions.append((1. / p))
                ps.append(p)
                rr.append((1. / p))
            else:
                print("Mutation file", file)
                print("Scores: ", scores[0:5])
                positions.append(0)
                ps.append('>100')
                rr.append(0)

        return np.mean(positions), ps, rr


#fstats_all = os.path.join(DATASET, 'repo-ecore-all/analysis/stats.txt')
#drepo_txt  = os.path.join(MUTANTS, 'search-mutants/txt/repo-ecore-all')
def read_text_files(stats_file, txt_folder):
    repo_ok = pd.read_csv(stats_file,
                          names=['localFile', 'total', 'packages', 'classes', 'references', 'attributes', 'enums',
                                 'enumLiterals', 'annotations'])

    import os
    import re
    titles = []  # titles
    docs = []  # content of documents
    for f in list(repo_ok['localFile']):
        prefix = txt_folder
        basename = os.path.basename(f)
        name = os.path.splitext(basename)[0]
        try:
            with open(prefix + '/' + f + '/' + name + '.txt', 'r') as file:
                data = file.read()
                docs.append(data)  # re.sub(r'[^a-zA-Z0-9]', ' ', data)
            titles.append(f)
        except:
            continue

    return titles, docs


def get_experiments(dmutants, stats_dataset):
    experiment = []
    import os
    for root, subdirs, files in os.walk(dmutants):  # change path
        if (files != [] and ('mutations.csv' in files)):
            csv = pd.read_csv(root + '/mutations.csv', names=['original', 'name', 'operation'])
            try:
                original = csv.values[0][0]
            except:
                continue

            # filter small and tiny, eliminate
            # if len(csv.index) ==1:
            # continue
            #if original in list(repo_ecore_ok["localFile"]) or original in list(atlanmod_ok["localFile"]):
            if original in list(stats_dataset["localFile"]):
                mut_name = root + '/mutations.csv'
                roott = root
                experiment.append((roott, mut_name, files))
    return experiment


def perform_evaluation(sample, dmutants_txt):
    mar_evaluation = MAREvaluation()

    mrrs = []
    mrrs_w = []
    mrrs_ps = []
    mrrs_w_ps = []

    RR_MAR = []
    RR_WHOOSH = []

    MAR_better = []
    WHOOSH_better = []
    both_same = []

    pos_MAR = []

    counter = 0
    for root, str_csv, files in sample:
        csv = pd.read_csv(str_csv, names=['original', 'name', 'operation'])
        try:
            original = csv.values[0][0]
        except:
            continue

        mutations = [f for f in files if f != 'mutations.csv']

        pref_mut = dmutants_txt + '/' + original  # change path

        mutations_ecore = [root + '/' + f for f in files if f != 'mutations.csv']
        mutations_txt = [pref_mut + '/' + f + '/' + f[:-6] + '.txt' for f in mutations]

        # if (len(mutations) == 1):
        #   name_mut = mutations[0]
        #  if ('.tiny.' in name_mut):
        #     continue
        # if ('.small.' in name_mut):
        #   continue

        # if (len(mutations)!=3):
        # continue

        # mutations_ecore = [f for f in mutations_ecore if ('.small.' in f) ]
        # mutations_txt = [f for f in mutations_txt if ('.small.' in f) ]

        try:
            #print(original, mutations_ecore)
            mm, ps1, rr_m = mar_evaluation.search_mutations(original, mutations_ecore)
            #print(mm, ps1, rr_m)
        #    mm, ps1, rr_m = mediaMRR(original, mutations_ecore)
        #    mw, ps2, rr_w = mediaMRRWhoosh(original, mutations_txt)
        except:
            import sys
            import traceback
            # print(sys.exc_info()[0])
            traceback.print_exc(file=sys.stdout)
            print('exception in ', original)
            #continue
            break

        # if (rr_m != rr_w):
        mrrs.append(mm)
        #mrrs_w.append(mw)
        mrrs_ps.append(ps1)
        #mrrs_w_ps.append(ps2)
        RR_MAR.append(rr_m)
        #RR_WHOOSH.append(rr_w)

        counter = counter + 1
        # print(counter, ": ", original)
        print('MAR: ', np.mean(np.array([item for sublist in RR_MAR for item in sublist])), len(MAR_better))
        #print('WHOOSH: ', np.mean(np.array([item for sublist in RR_WHOOSH for item in sublist])), len(WHOOSH_better))


def main(args):
    repo_root = '/home/jesus/projects/mde-ml/mde-datasets'
    experiments_root = '/home/jesus/projects/mde-ml/mar-experiments'

    dmutants = os.path.join(experiments_root, 'search-mutants/mutants-connected/repo-ecore-all-connected')
    dmutants_txt = os.path.join(experiments_root, 'search-mutants/txt/mutants-connected/repo-ecore-all-connected')
    # "/home/jesus/projects/mde-ml/mar-experiments/search-mutants/mutants-connected/repo-ecore-all-connected"

    #mutants = os.path.join(experiments_root, 'search-mutants/mutants-sized/repo-ecore-all-connected')
    #dmutants_txt = os.path.join(experiments_root, 'mar-experiments/search-mutants/txt/mutants-sized/repo-ecore-all-connected')

    fstats_all = os.path.join(repo_root, 'repo-ecore-all/analysis/stats.txt')

    dataset = pd.read_csv(fstats_all,
                          names=['localFile', 'total', 'packages', 'classes', 'references', 'attributes', 'enums',
                                 'enumLiterals', 'annotations'])

    experiments = get_experiments(dmutants, dataset)

    #import random
    #random.seed(10)
    #experiments = random.sample(experiments, 200)
    
    perform_evaluation(experiments, dmutants_txt)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Evaluate MAR')
    #parser.add_argument('--mode', type=str, default='token-id',
    #                    choices=['all', 'all-sample', 'token-id', 'line', 'token', 'block', 'performance'])
    #parser.add_argument('--results', required=True)
    #parser.add_argument('--sort', required=False)
    #parser.add_argument('--mapping', required=False, default='mapping.yaml')
    #parser.add_argument('--language', required=False)
    args = parser.parse_args()

    main(args)
