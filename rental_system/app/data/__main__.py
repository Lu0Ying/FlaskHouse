"""
app.data.__main__ module
允许使用 `python -m app.data` 运行初始化
"""

from . import init_regions_data

if __name__ == '__main__':
    print('开始初始化行政区划数据...')
    success = init_regions_data()
    import sys
    sys.exit(0 if success else 1)