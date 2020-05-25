import json
import pickle
from indra.belief import BeliefEngine
from indra.sources import indra_db_rest

# List of entities that are not of interest to get INDRA Statements
# e.g., ATP, oxygen
black_list = {
    'CHEBI:58245',
    'CHEBI:57673',
    'CHEBI:30616',
    'CHEBI:16174',
    'CHEBI:35782',
    'CHEBI:10545',
    'CHEBI:65180',
    'CHEBI:57600',
    'CHEBI:58115',
    'CHEBI:64428',
    'CHEBI:15422',
    'CHEBI:15379',
    'CHEBI:16856',
    'CHEBI:29036',
    'CHEBI:16234',
    'CHEBI:17245',
    'CHEBI:17992',
    'CHEBI:18367',
    'CHEBI:16761',
    'CHEBI:16474',
    'CHEBI:16335',
    'CHEBI:15996',
    'CHEBI:15846',
    'CHEBI:29356',
    'CHEBI:17552',
    'CHEBI:16708',
    'CHEBI:16235',
    'CHEBI:15377',
    'CHEBI:15713',
    'CHEBI:16526',
    'CHEBI:33699',
    'CHEBI:17659',
    'CHEBI:16284',
    'CHEBI:15378',
    'CHEBI:456216',
    'CHEBI:456215',
    'CHEBI:16908',
    'CHEBI:16750',
    'CHEBI:29235',
    'CHEBI:16497',
    'CHEBI:13389',
    'CHEBI:28862',
    'CHEBI:25523',
}


def get_stmts_by_grounding(db_ns, db_id):
    ip = indra_db_rest.get_statements(agents=['%s@%s' % (db_id, db_ns)],
                                      ev_limit=100)
    print('%d statements for %s:%s' % (len(ip.statements), db_ns, db_id))
    return ip.statements


def filter_prior_all(stmts, groundings):
    groundings = {tuple(g[:2]) for g in groundings}
    filtered_stmts = []
    for stmt in stmts:
        stmt_groundings = {a.get_grounding() for a in stmt.agent_list()
                           if a is not None}
        if stmt_groundings <= groundings:
            filtered_stmts.append(stmt)
    return filtered_stmts


def make_unique_hashes(stmts):
    return list({stmt.get_hash(): stmt for stmt in stmts}.values())


def reground_stmts(stmts, gm):
    for stmt in stmts:
        for agent in stmt.agent_list():
            if agent is not None:
                txt = agent.db_refs.get('TEXT')
                if txt and txt in gm:
                    agent.db_refs = {'TEXT': txt}
                    agent.db_refs.update(gm[txt])


if __name__ == '__main__':
    with open('minerva_disease_map_indra_ids.csv', 'r') as fh:
        groundings = [line.strip().split(',') for line in fh.readlines()]
    all_stmts = []
    for db_ns, db_id, name in groundings:
        if db_id in black_list:
            print('Skipping %s in black list' % name)
            continue
        print('Looking up %s' % name)
        all_stmts += get_stmts_by_grounding(db_ns, db_id)
    all_stmts = make_unique_hashes(all_stmts)

    with open('../../grounding_map.json', 'r') as fh:
        gm = json.load(fh)

    reground_stmts(all_stmts, gm)
    be = BeliefEngine()
    be.set_prior_probs(all_stmts)

    with open('disease_map_indra_stmts_full.pkl', 'wb') as fh:
        pickle.dump(all_stmts, fh)

    filtered_stmts = filter_prior_all(all_stmts, groundings)
    with open('disease_map_indra_stmts_filtered.pkl', 'wb') as fh:
        pickle.dump(filtered_stmts, fh)

