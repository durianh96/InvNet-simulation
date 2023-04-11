import numpy as np
import pandas as pd

DEFAULT_NORMAL_MEAN = 10
DEFAULT_NORMAL_STD = 2


def normal_ds_generating(normal_mean=DEFAULT_NORMAL_MEAN, normal_std=DEFAULT_NORMAL_STD, sample_size=1):
    ds = [round(i, 2) for i in np.random.normal(normal_mean, normal_std, sample_size)]
    if len(ds) == 1:
        ds = ds[0]
    return ds


def single_records_info_to_df(sn):
    on_hand_begin = pd.DataFrame(sn.records['on_hand_begin'],
                                 columns=['time_step', 'on_hand_begin']).set_index('time_step')
    inv_pos_begin = pd.DataFrame(sn.records['inv_pos_begin'],
                                 columns=['time_step', 'inv_pos_begin']).set_index('time_step')
    backorder_begin = pd.DataFrame(sn.records['backorder_begin'],
                                   columns=['time_step', 'backorder_begin']).set_index('time_step')
    working_inv_sum_begin = pd.DataFrame(sn.records['working_inv_sum_begin'],
                                         columns=['time_step', 'working_inv_sum_begin']).set_index('time_step')
    demand_sample = pd.DataFrame(sn.records['demand_sample'],
                                 columns=['time_step', 'demand_sample']).set_index('time_step')
    fill_qty = pd.DataFrame(sn.records['fill_qty'],
                            columns=['time_step', 'fill_to', 'fill_qty']).set_index('time_step')
    plan_qty = pd.DataFrame(sn.records['plan_qty'],
                            columns=['time_step', 'plan_qty']).set_index('time_step')

    on_hand_end = pd.DataFrame(sn.records['on_hand_end'],
                               columns=['time_step', 'on_hand_end']).set_index('time_step')
    inv_pos_end = pd.DataFrame(sn.records['inv_pos_end'],
                               columns=['time_step', 'inv_pos_end']).set_index('time_step')
    backorder_end = pd.DataFrame(sn.records['backorder_end'],
                                 columns=['time_step', 'backorder_end']).set_index('time_step')
    working_inv_sum_end = pd.DataFrame(sn.records['working_inv_sum_end'],
                                       columns=['time_step', 'working_inv_sum_end']).set_index('time_step')

    records_df = pd.concat([on_hand_begin, inv_pos_begin, backorder_begin, working_inv_sum_begin,
                            demand_sample, fill_qty, plan_qty,
                            on_hand_end, inv_pos_end, backorder_end, working_inv_sum_end], axis=1).reset_index()
    return records_df
