#!/usr/bin/env python3

import json
import sys

from .kast      import *
from .kastManip import *

from .kast import _fatal, _notif, _warning

def getRuleById(definition, rule_id):
    """Get a rule from the definition by coverage rule id.

    Input:

        -   definition: json encoded definition.
        -   rule_id: string of unique rule identifier generated by `kompile --coverage`.

    Output: json encoded rule which has identifier rule_id.
    """

    for module in definition['modules']:
        for sentence in module['localSentences']:
            if isKRule(sentence) and 'att' in sentence:
                atts = sentence['att']['att']
                if 'UNIQUE_ID' in atts and atts['UNIQUE_ID'] == rule_id:
                    return sentence
    _fatal('Could not find rule with ID: ' + rule_id)

def stripCoverageLogger(rule):
    ruleBody     = rule["body"]
    ruleRequires = rule["requires"]
    ruleEnsures  = rule["ensures"]
    ruleAtts     = rule["att"]

    if isKRewrite(ruleBody):
        ruleLHS = ruleBody['lhs']
        ruleRHS = ruleBody['rhs']
        if isKApply(ruleRHS) and ruleRHS['label'].startswith('project:'):
            ruleRHSseq = ruleRHS['args'][0]
            if isKSequence(ruleRHSseq) and len(ruleRHSseq['items']) == 2:
                ruleBody = KRewrite(ruleLHS, ruleRHSseq['items'][1])
    return KRule(ruleBody, requires = ruleRequires, ensures = ruleEnsures, att = ruleAtts)

def translateCoverage(src_all_rules, dst_all_rules, dst_definition, src_rules_list):
    """Translate the coverage data from one kompiled definition to another.

    Input:

        -   src_all_rules: contents of allRules.txt for definition which coverage was generated for.
        -   dst_all_rules: contents of allRules.txt for definition which you desire coverage for.
        -   dst_definition: JSON encoded definition of dst kompiled definition.
        -   src_rules_list: Actual coverage data produced.

    Output: list of non-functional rules applied in dst definition translated from src definition.
    """

    # Load the src_rule_id -> src_source_location rule map from the src kompiled directory
    src_rule_map = {}
    for line in src_all_rules:
        [ src_rule_hash, src_rule_loc ] = line.split(' ')
        src_rule_loc = src_rule_loc.split('/')[-1]
        src_rule_map[src_rule_hash.strip()] = src_rule_loc.strip()

    # Load the dst_rule_id -> dst_source_location rule map (and inverts it) from the dst kompiled directory
    dst_rule_map = {}
    for line in dst_all_rules:
        [ dst_rule_hash, dst_rule_loc ] = line.split(' ')
        dst_rule_loc = dst_rule_loc.split('/')[-1]
        dst_rule_map[dst_rule_loc.strip()] = dst_rule_hash.strip()

    src_rule_list = [ rule_hash.strip() for rule_hash in src_rules_list ]

    # Filter out non-functional rules from rule map (determining if they are functional via the top symbol in the rule being `<generatedTop>`)
    dst_non_function_rules = []
    for module in dst_definition['modules']:
        for sentence in module['localSentences']:
            if isKRule(sentence):
                ruleBody = sentence['body']
                ruleAtt  = sentence['att']['att']
                if    (isKApply(ruleBody)                                 and ruleBody['label']        == '<generatedTop>') \
                   or (isKRewrite(ruleBody) and isKApply(ruleBody['lhs']) and ruleBody['lhs']['label'] == '<generatedTop>'):
                    if 'UNIQUE_ID' in ruleAtt:
                        dst_non_function_rules.append(ruleAtt['UNIQUE_ID'])

    # Convert the src_coverage rules to dst_no_coverage rules via the maps generated above
    dst_rule_list = []
    for src_rule in src_rule_list:
        if src_rule not in src_rule_map:
            _fatal('COULD NOT FIND RULE IN src_rule_map: ' + src_rule)
        src_rule_loc = src_rule_map[src_rule]

        if src_rule_loc not in dst_rule_map:
            _fatal('COULD NOT FIND RULE LOCATION IN dst_rule_map: ' + src_rule_loc)
        dst_rule = dst_rule_map[src_rule_loc]

        if dst_rule not in dst_non_function_rules:
            _notif('Skipping non-semantic rule: ' + dst_rule)
        else:
            dst_rule_list.append(dst_rule)

    return dst_rule_list

def translateCoverageFromPaths(src_kompiled_dir, dst_kompiled_dir, src_rules_file):
    """Translate coverage information given paths to needed files.

    Input:

        -   src_kompiled_dir: Path to *-kompiled directory of source.
        -   dst_kompiled_dir: Path to *-kompiled directory of destination.
        -   src_rules_file: Path to generated rules coverage file.

    Output: Translated list of rules with non-semantic rules stripped out.
    """
    src_all_rules = []
    with open(src_kompiled_dir + '/allRules.txt', 'r') as src_all_rules_file:
        src_all_rules = [ line.strip() for line in src_all_rules_file ]

    dst_all_rules = []
    with open(dst_kompiled_dir + '/allRules.txt', 'r') as dst_all_rules_file:
        dst_all_rules = [ line.strip() for line in dst_all_rules_file ]

    dst_definition = readKastTerm(dst_kompiled_dir + '/compiled.json')

    src_rules_list = []
    with open(src_rules_file, 'r') as src_rules:
        src_rules_list = [ line.strip() for line in src_rules ]

    return translateCoverage(src_all_rules, dst_all_rules, dst_definition, src_rules_list)