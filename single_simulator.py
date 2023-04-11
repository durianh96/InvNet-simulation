from sim_node import *
from default_sim_paras import *
from typing import Union
from sim_utils import *


class SingleEvaluator:
    def __init__(self, node_id: str, oul: Union[int, float],
                 rop: Union[int, float] = None,
                 lt: Union[int, float] = DEFAULT_LT,
                 review_cycle: int = DEFAULT_REVIEW_CYCLE,
                 sim_steps_num: int = DEFAULT_SIM_STEPS_NUM,
                 sim_unit: int = DEFAULT_SIM_UNIT,
                 backorder: bool = True):

        time_index = list(range(sim_steps_num))
        decision_time_steps = [i for i, t in enumerate(time_index) if (t % review_cycle == 0) and (t > 0)]

        self.sim_node = EvaNode(node_id, lt, sim_steps_num, decision_time_steps, sim_unit)
        self.external_demand_samples = normal_ds_generating(sample_size=sim_steps_num)
        self.oul = oul
        if rop is None:
            self.rop = oul
        else:
            self.rop = rop
        self.backorder = backorder

    def run(self):
        for i in range(self.sim_node.sim_steps_num):
            self.sim_one_step()
        records_df = single_records_info_to_df(self.sim_node)
        return records_df

    def sim_one_step(self):
        # receive working inventory
        receive_working_inv(self.sim_node)
        # record inventory status at the beginning of this time step
        record_begin_inv_status(self.sim_node)

        # fulfill demand
        ds = self.external_demand_samples[self.sim_node.time_step]
        if self.backorder:
            fulfill_external_demand_backorder(self.sim_node, ds)
        else:
            fulfill_external_demand_lostsales(self.sim_node, ds)

        if (self.sim_node.time_step in self.sim_node.decision_time_steps) and (self.sim_node.inv_pos < self.rop):
            plan_qty = self.oul - self.sim_node.inv_pos
            update_plan_qty(self.sim_node, plan_qty)
        else:
            skip_plan(self.sim_node)

        # record inventory status at the end of this time step
        record_end_inv_status(self.sim_node)

        # update time step
        self.sim_node.time_step += 1


if __name__ == '__main__':
    # oul-T backorder system
    simulator1 = SingleEvaluator(node_id='n01', oul=45, lt=2, sim_steps_num=180, sim_unit=1,
                                 review_cycle=3, backorder=True)
    records1_df = simulator1.run()

    # rop-oul-T backorder system
    simulator1 = SingleEvaluator(node_id='n01', rop=10, oul=45, lt=2, sim_steps_num=180, sim_unit=1,
                                 review_cycle=3, backorder=True)
    records2_df = simulator1.run()
