#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
import pybullet as p
import pybullet_data
import os
import time
from ament_index_python.packages import get_package_share_directory


class UnifiedPyBulletController(Node):
    def __init__(self):
        super().__init__('unified_pybullet_controller')

        # PyBullet GUI and setup
        p.connect(p.GUI)
        p.setGravity(0, 0, -9.81)
        p.setAdditionalSearchPath(pybullet_data.getDataPath())

        # Load robot and warehouse world
        self.world1_urdf_path = self.get_model_path('world1_description', 'urdf/world1.urdf')
        script_dir = os.path.dirname(os.path.realpath(__file__))
        workspace_root = os.path.abspath(os.path.join(script_dir, '../../../'))
        warehouse_model_path = os.path.join(workspace_root, 'aws_robomaker_small_warehouse_world',
                                            'share', 'aws_robomaker_small_warehouse_world', 'models')

        self.shelf_path = self.check_path(os.path.join(warehouse_model_path, 'aws_robomaker_warehouse_ShelfF_01/model.urdf'))
        self.pallet_path = self.check_path(os.path.join(warehouse_model_path, 'aws_robomaker_warehouse_PalletJackB_01/model.urdf'))
        self.trashcan_path = self.check_path(os.path.join(warehouse_model_path, 'aws_robomaker_warehouse_TrashCanC_01/model.urdf'))
        self.clutter_path = self.check_path(os.path.join(warehouse_model_path, 'aws_robomaker_warehouse_ClutteringA_01/model.urdf'))
        self.cube_path = self.check_path(os.path.join(warehouse_model_path, 'cube.urdf'))
        self.table_path = os.path.join(pybullet_data.getDataPath(), 'table', 'table.urdf')

        self.load_models()


    def get_model_path(self, package_name, relative_path):
        pkg_share = get_package_share_directory(package_name)
        abs_path = os.path.join(pkg_share, relative_path)
        return self.check_path(abs_path)

    def check_path(self, path):
        if not os.path.exists(path):
            self.get_logger().error(f"URDF file not found: {path}")
            raise FileNotFoundError(path)
        return path

    def load_models(self):
        
        self.world1_id = p.loadURDF(self.world1_urdf_path, basePosition=[0, 0, -0.05], useFixedBase=True)
        self.left_wheel_joint = 18
        self.right_wheel_joint = 17

        for pos in [[-8.5, 1, 0], [8.5, -16, 0], [1.2, -16, 0], [7, 15, 0], [17, 8, 0]]:
            p.loadURDF(self.shelf_path, basePosition=pos, useFixedBase=True)

        for pos in [[-4, 7.5, 0], [-3, 7.5, 0]]:
            p.loadURDF(self.pallet_path, basePosition=pos, useFixedBase=True)

        for pos in [[-1.5, 7.5, 0], [1.0, 8, 0], [1.0, 9, 0], [1.0, 10, 0]]:
            p.loadURDF(self.trashcan_path, basePosition=pos, useFixedBase=True)

        for pos in [[-6, -7, 0], [-3, -7, 0], [-1, -7, 0], [-6, 7.5, 0], [-3, 3, 0], [-5, 3, 0], [-5, 1, 0]]:
            p.loadURDF(self.clutter_path, basePosition=pos, useFixedBase=True)

        for pos in [[0, -3, 0], [3, 0, 0], [-2, -3, 0], [2, -3, 0]]:
            p.loadURDF(self.table_path, basePosition=pos, useFixedBase=True)

        p.loadURDF(self.cube_path, basePosition=[0, -2.8, 1], useFixedBase=False)
        self.get_logger().info("All models loaded successfully.")
        time.sleep(1)


def main(args=None):
    rclpy.init(args=args)
    node = UnifiedPyBulletController()

    try:
        while rclpy.ok():
            rclpy.spin_once(node, timeout_sec=0)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
        p.disconnect()

if __name__ == '__main__':
    main()
