"""
HomePod 配对工具
首次使用 pyatv 控制 HomePod 时需要进行配对
"""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()


async def pair_device(ip: str, name: str = None):
    """配对指定 IP 的 HomePod"""
    try:
        import pyatv
        from pyatv import pair

        loop = asyncio.get_event_loop()

        # 扫描设备
        print(f"正在扫描 {ip}...")
        atvs = await pyatv.scan(loop, hosts=[ip])

        if not atvs:
            print(f"未找到设备: {ip}")
            return False

        atv = atvs[0]
        print(f"发现设备: {atv.name} ({atv.address})")

        # 开始配对 (使用 AirPlay 协议)
        pairing = await pair(atv, loop, "airplay")

        print("请输入 HomePod 屏幕上显示的 PIN 码...")

        async with pairing:
            await pairing.begin()

            # 等待用户输入 PIN
            pin = input("PIN: ")
            pairing.pin(pin)

            await pairing.finish()

            if pairing.has_paired:
                print("配对成功!")
                # 获取 credentials
                for service in atv.services:
                    if service.service_type == "airplay":
                        print(f"AirPlay Credentials: {service.credentials}")
                        print(f"\n请将此 credentials 保存到 .env 文件:")
                        print(f"AIRPLAY_CREDENTIALS_{name or 'DEFAULT}={service.credentials}")
                return True
            else:
                print("配对失败")
                return False

    except Exception as e:
        print(f"配对错误: {e}")
        return False


async def scan_all():
    """扫描局域网所有 AirPlay 设备"""
    try:
        import pyatv

        loop = asyncio.get_event_loop()
        print("正在扫描局域网...")
        atvs = await pyatv.scan(loop)

        if not atvs:
            print("未发现任何设备")
            return

        print(f"\n发现 {len(atvs)} 个设备:\n")
        for i, atv in enumerate(atvs, 1):
            print(f"{i}. {atv.name}")
            print(f"   IP: {atv.address}")
            print(f"   ID: {atv.identifier}")
            print(f"   服务: {[s.service_type for s in atv.services]}")
            print()

    except Exception as e:
        print(f"扫描错误: {e}")


async def main():
    print("=" * 50)
    print("HomePod 配对工具")
    print("=" * 50)
    print()
    print("1. 扫描局域网设备")
    print("2. 配对指定设备")
    print("3. 退出")
    print()

    choice = input("请选择 (1-3): ").strip()

    if choice == "1":
        await scan_all()
    elif choice == "2":
        ip = input("请输入 HomePod IP 地址: ").strip()
        name = input("请输入设备名称 (如: 客厅): ").strip() or None
        await pair_device(ip, name)
    elif choice == "3":
        print("再见!")
    else:
        print("无效选择")


if __name__ == "__main__":
    asyncio.run(main())
