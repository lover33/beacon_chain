import copy

import pytest

from beacon_chain.utils.blake import blake
from beacon_chain.utils.simpleserialize import (
    serialize,
)

from beacon_chain.state.state_transition import (
    fill_recent_block_hashes,
    get_recalculated_states,
    initialize_new_cycle,
)


@pytest.mark.parametrize(
    'attestation_slot,block_slot_number,is_valid',
    [
        (5, 4, False),
        (6, 6, False),
        (6, 7, True),
        (1, 10, True),
    ]
)
def test_validate_attestation_slot(attestation_slot,
                                   block_slot_number,
                                   is_valid,
                                   sample_attestation_record_params,
                                   sample_block_params,
                                   sample_crystallized_state_params):
    pass


def test_validate_attestation_bitfield():
    pass


def test_validate_attestation_aggregate_sig():
    pass


@pytest.mark.parametrize(
    (
        'cycle_length,last_state_recalc,'
        'last_justified_slot,justified_streak,last_finalized_slot,'
        'crystallized_state_total_deposits,block_vote_cache_total_deposits,'
        'result_last_state_recalc,result_justified_streak, result_last_finalized_slot'
    ),
    [
        (64, 0, 0, 0, 0, 3, 2, 64, 0+64, 0),  # 2/3 attestations
        (64, 0, 0, 0, 0, 3, 1, 64, 0+0, 0),   # 1/3 attestations
        (64, 128, 128, 64, 0, 3, 2, 128+64, 64+64, 127-64-1),  # 2/3 attestations, last_finalized_slot = slot - cycle_length - 1
        (64, 128, 128, 128, 128, 3, 2, 128+64, 128+64, 128),  # 2/3 attestations, last_finalized_slot = last_finalized_slot
    ],
)
def test_initialize_new_cycle(genesis_crystallized_state,
                              genesis_active_state,
                              genesis_block,
                              last_state_recalc,
                              last_justified_slot,
                              justified_streak,
                              last_finalized_slot,
                              crystallized_state_total_deposits,
                              block_vote_cache_total_deposits,
                              result_last_state_recalc,
                              result_justified_streak,
                              result_last_finalized_slot,
                              config):
    # Fill the parent_crystallized_state with parematers
    parent_crystallized_state = genesis_crystallized_state
    parent_crystallized_state.last_state_recalc = last_state_recalc
    parent_crystallized_state.last_justified_slot = last_justified_slot
    parent_crystallized_state.justified_streak = justified_streak
    parent_crystallized_state.last_finalized_slot = last_finalized_slot
    parent_crystallized_state.total_deposits = crystallized_state_total_deposits

    parent_active_state = genesis_active_state

    parent_block = genesis_block
    block = copy.deepcopy(genesis_block)
    block.slot_number = 258
    block.parent_hash = blake(serialize(parent_block))

    active_state = fill_recent_block_hashes(
        parent_active_state, parent_block, block
    )
    # Fill the total_voter_deposits to simulate the different committee results
    active_state.block_vote_cache[block.parent_hash] = {
        'voter_indices': set(),
        'total_voter_deposits': block_vote_cache_total_deposits,
    }

    crystallized_state, active_state = initialize_new_cycle(
        parent_crystallized_state,
        active_state,
        block,
        config=config,
    )
    assert crystallized_state.last_state_recalc == result_last_state_recalc
    assert crystallized_state.justified_streak == result_justified_streak
    assert crystallized_state.last_finalized_slot == result_last_finalized_slot


def test_get_recalculated_states(genesis_crystallized_state,
                                 genesis_active_state,
                                 genesis_block,
                                 config):
    parent_crystallized_state = genesis_crystallized_state
    parent_active_state = genesis_active_state
    parent_block = genesis_block
    block = copy.deepcopy(genesis_block)
    block.slot_number = 258

    active_state = fill_recent_block_hashes(
        parent_active_state, parent_block, block
    )
    crystallized_state, active_state = get_recalculated_states(
        parent_crystallized_state,
        active_state,
        block,
        config=config,
    )
    assert crystallized_state.last_state_recalc == (
        block.slot_number // config['cycle_length'] * config['cycle_length']
    )
