"""
routers 层负责定义 HTTP 接口、参数绑定和响应输出，是 API 对外入口。

通过 Depends 调用 deps 层提供的依赖（DB、鉴权、service 实例）。
将具体业务处理委托给 services 层，并使用 schemas 层约束输入输出。

"""
