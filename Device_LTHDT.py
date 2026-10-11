""" Mã sinh viên: 202419115
 Họ tên: Đoàn Anh Tuấn """


from __future__ import annotations

import ipaddress
import math
import textwrap
from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal
from enum import Enum
from itertools import zip_longest
from typing import Callable, List, Optional, Tuple


def currentYear() -> int:
    return date.today().year


def vnd(amount) -> str:
    """Định dạng tiền kiểu Việt Nam: 2.100.000 (chỉ hiện phần lẻ nếu có)."""
    value = Decimal(str(amount)).quantize(Decimal("0.01"))
    text = f"{value:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
    return text[:-3] if text.endswith(",00") else text


def _text(value, name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} phải là chuỗi (str)")
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{name} không được rỗng")
    return cleaned


def _money(value, name: str) -> Decimal:
    """Số tiền > 0, trả về Decimal (float được đổi qua chuỗi để không lệch)."""
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        raise TypeError(f"{name} phải là số")
    number = Decimal(str(value)) if isinstance(value, float) else Decimal(value)
    if not number.is_finite():
        raise ValueError(f"{name} phải là số hữu hạn")
    if number <= 0:
        raise ValueError(f"{name} phải lớn hơn 0")
    return number


def _integer(value, name: str, minimum: int, strict_greater: bool = False) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} phải là số nguyên")
    if value < minimum or (strict_greater and value == minimum):
        word = "lớn hơn" if strict_greater else "không nhỏ hơn"
        raise ValueError(f"{name} phải {word} {minimum}")
    return value


def _real(value, name: str, minimum: float, strict_greater: bool = False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} phải là số")
    if not math.isfinite(value):
        raise ValueError(f"{name} phải là số hữu hạn")
    if value < minimum or (strict_greater and value == minimum):
        word = "lớn hơn" if strict_greater else "không nhỏ hơn"
        raise ValueError(f"{name} phải {word} {minimum}")
    return value


def _bool(value, name: str) -> bool:
    if not isinstance(value, bool):
        raise TypeError(f"{name} phải là bool")
    return value


def _year(value) -> int:
    year = _integer(value, "Năm đưa vào sử dụng", Device.MIN_YEAR)
    if year > currentYear():
        raise ValueError("Năm đưa vào sử dụng không được lớn hơn năm hiện tại")
    return year


def _ip(value) -> str:
    text = _text(value, "Địa chỉ IP")
    try:
        ipaddress.ip_address(text)
    except ValueError:
        raise ValueError(f"Địa chỉ IP không đúng định dạng: '{text}'") from None
    return text

class DeviceStatus(Enum):
    Active = "Active"
    UnderMaintenance = "UnderMaintenance"
    Retired = "Retired"


class PrinterType(Enum):
    Laser = "Laser"
    Inkjet = "Inkjet"


class DeviceStateError(RuntimeError):
    """Thao tác không hợp lệ với trạng thái hiện tại (vd. kết nối khi đang kết nối)."""


# Interface INetworkable
class INetworkable(ABC):
    """Năng lực kết nối mạng, độc lập với cây kế thừa Device."""

    @property
    @abstractmethod
    def ipAddress(self) -> Optional[str]:
        """Địa chỉ IP đang hoạt động; None nếu chưa kết nối."""

    @property
    @abstractmethod
    def isConnected(self) -> bool: ...

    @abstractmethod
    def connect(self, ipAddress: str) -> None: ...

    @abstractmethod
    def disconnect(self) -> None: ...


class NetworkConnection(INetworkable):
    """Thành phần giữ trạng thái kết nối (dùng chung, tránh lặp logic)."""

    def __init__(self):
        self._ip: Optional[str] = None

    @property
    def ipAddress(self) -> Optional[str]:
        return self._ip

    @property
    def isConnected(self) -> bool:
        return self._ip is not None

    def connect(self, ipAddress: str) -> None:
        if self.isConnected:
            raise DeviceStateError(
                f"Thiết bị đang kết nối với {self._ip}; hãy disconnect() trước")
        self._ip = _ip(ipAddress)      

    def disconnect(self) -> None:
        self._ip = None                 


class NetworkCapable(INetworkable):
    """Mixin: hiện thực INetworkable bằng cách ỦY QUYỀN cho self._connection."""

    _connection: NetworkConnection

    @property
    def ipAddress(self) -> Optional[str]:
        return self._connection.ipAddress

    @property
    def isConnected(self) -> bool:
        return self._connection.isConnected

    def connect(self, ipAddress: str) -> None:
        self._connection.connect(ipAddress)

    def disconnect(self) -> None:
        self._connection.disconnect()

    def _networkInfo(self) -> str:
        return f"Mạng: {self.ipAddress}" if self.isConnected else "Mạng: chưa kết nối"



# Lớp trừu tượng Device
class Device(ABC):
    MIN_YEAR = 1900
    OLD_AGE_YEARS = 5               

    def __init__(self, deviceId: str, name: str, yearInUse: int,
                 purchasePrice, status: DeviceStatus = DeviceStatus.Active):
        deviceId = _text(deviceId, "Mã thiết bị")
        name = _text(name, "Tên thiết bị")
        yearInUse = _year(yearInUse)
        purchasePrice = _money(purchasePrice, "Giá mua")
        if not isinstance(status, DeviceStatus):
            raise TypeError("Trạng thái phải là DeviceStatus")

        self._deviceId: str = deviceId
        self._name: str = name
        self._yearInUse: int = yearInUse
        self._purchasePrice: Decimal = purchasePrice
        self._status: DeviceStatus = status

    # ---- Thuộc tính ----
    @property
    def deviceId(self) -> str:                 
        return self._deviceId

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = _text(value, "Tên thiết bị")

    @property
    def yearInUse(self) -> int:
        return self._yearInUse

    @property
    def purchasePrice(self) -> Decimal:
        return self._purchasePrice

    @property
    def status(self) -> DeviceStatus:
        return self._status

    @status.setter
    def status(self, value: DeviceStatus) -> None:
        if not isinstance(value, DeviceStatus):
            raise TypeError("Trạng thái phải là DeviceStatus")
        self._status = value

    @property
    def ageInYears(self) -> int:
        return currentYear() - self._yearInUse

    def isOld(self) -> bool:
        """Đã sử dụng trên 5 năm."""
        return self.ageInYears > self.OLD_AGE_YEARS

    def requiresMaintenance(self) -> bool:
        return self._status is DeviceStatus.UnderMaintenance or self.isOld()

    @abstractmethod
    def calculateAnnualMaintenanceCost(self) -> Decimal:
        """Chi phí bảo trì dự kiến trong một năm."""

    def __str__(self) -> str:
        return (f"[{type(self).__name__}] {self._deviceId} - {self._name}"
                f" | Năm: {self._yearInUse} ({self.ageInYears} năm)"
                f" | Giá: {vnd(self._purchasePrice)}"
                f" | {self._status.name}"
                f" | Bảo trì/năm: {vnd(self.calculateAnnualMaintenanceCost())}")



# Computer
class Computer(Device, NetworkCapable):
    BASE_RATE = Decimal("0.05")
    GPU_RATE = Decimal("0.02")
    OLD_RATE = Decimal("0.01")

    def __init__(self, deviceId, name, yearInUse, purchasePrice,
                 ramGb: int, processor: str, hasDiscreteGpu: bool,
                 status: DeviceStatus = DeviceStatus.Active):
        ramGb = _integer(ramGb, "Dung lượng RAM", 0, strict_greater=True)
        processor = _text(processor, "Loại bộ xử lý")
        hasDiscreteGpu = _bool(hasDiscreteGpu, "hasDiscreteGpu")
        super().__init__(deviceId, name, yearInUse, purchasePrice, status)
        self._ramGb = ramGb
        self._processor = processor
        self._hasDiscreteGpu = hasDiscreteGpu
        self._connection = NetworkConnection()

    @property
    def ramGb(self) -> int:
        return self._ramGb

    @property
    def processor(self) -> str:
        return self._processor

    @property
    def hasDiscreteGpu(self) -> bool:
        return self._hasDiscreteGpu

    def calculateAnnualMaintenanceCost(self) -> Decimal:
        rate = self.BASE_RATE
        if self._hasDiscreteGpu:
            rate += self.GPU_RATE
        if self.isOld():
            rate += self.OLD_RATE
        return self._purchasePrice * rate

    def __str__(self) -> str:
        gpu = "Có" if self._hasDiscreteGpu else "Không"
        return (f"{super().__str__()} | RAM: {self._ramGb}GB | CPU: {self._processor}"
                f" | GPU rời: {gpu} | {self._networkInfo()}")



# Printer và NetworkPrinter
class Printer(Device):
    BASE_RATE = Decimal("0.04")
    HIGH_VOLUME_PAGES = 100_000
    HIGH_VOLUME_SURCHARGE = Decimal("500000")
    COLOR_SURCHARGE = Decimal("300000")

    def __init__(self, deviceId, name, yearInUse, purchasePrice,
                 printerType: PrinterType, pagesPrinted: int, isColor: bool,
                 status: DeviceStatus = DeviceStatus.Active):
        if not isinstance(printerType, PrinterType):
            raise TypeError("Loại máy in phải là PrinterType")
        pagesPrinted = _integer(pagesPrinted, "Số trang đã in", 0)
        isColor = _bool(isColor, "isColor")
        super().__init__(deviceId, name, yearInUse, purchasePrice, status)
        self._printerType = printerType
        self._pagesPrinted = pagesPrinted
        self._isColor = isColor

    @property
    def printerType(self) -> PrinterType:
        return self._printerType

    @property
    def pagesPrinted(self) -> int:
        return self._pagesPrinted

    @property
    def isColor(self) -> bool:
        return self._isColor

    @property
    def supportsNetwork(self) -> bool:
        """Suy ra từ kiểu: máy in thường không có mạng."""
        return False

    def recordPrinting(self, pages: int) -> None:
        self._pagesPrinted += _integer(pages, "Số trang in thêm", 0,
                                       strict_greater=True)

    def calculateAnnualMaintenanceCost(self) -> Decimal:
        cost = self._purchasePrice * self.BASE_RATE
        if self._pagesPrinted > self.HIGH_VOLUME_PAGES:
            cost += self.HIGH_VOLUME_SURCHARGE
        if self._isColor:
            cost += self.COLOR_SURCHARGE
        return cost

    def __str__(self) -> str:
        color = "màu" if self._isColor else "đen trắng"
        return (f"{super().__str__()} | {self._printerType.name} {color}"
                f" | Đã in: {vnd(self._pagesPrinted)} trang"
                f" | Hỗ trợ mạng: {'Có' if self.supportsNetwork else 'Không'}")


class NetworkPrinter(Printer, NetworkCapable):
    """Máy in có khả năng mạng: Printer + INetworkable."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._connection = NetworkConnection()

    @property
    def supportsNetwork(self) -> bool:
        return True

    def __str__(self) -> str:
        return f"{super().__str__()} | {self._networkInfo()}"


# Projector
class Projector(Device):
    BASE_RATE = Decimal("0.03")
    LAMP_LIMIT_HOURS = 3_000
    LAMP_SURCHARGE = Decimal("1500000")

    def __init__(self, deviceId, name, yearInUse, purchasePrice,
                 brightnessLumens: int, lampHours: float,
                 status: DeviceStatus = DeviceStatus.Active):
        brightnessLumens = _integer(brightnessLumens, "Độ sáng (lumen)", 0,
                                    strict_greater=True)
        lampHours = _real(lampHours, "Số giờ dùng bóng đèn", 0)
        super().__init__(deviceId, name, yearInUse, purchasePrice, status)
        self._brightnessLumens = brightnessLumens
        self._lampHours = lampHours

    @property
    def brightnessLumens(self) -> int:
        return self._brightnessLumens

    @property
    def lampHours(self) -> float:
        return self._lampHours

    def addLampHours(self, hours: float) -> None:
        self._lampHours += _real(hours, "Số giờ thêm", 0, strict_greater=True)

    def replaceLamp(self) -> None:
        self._lampHours = 0

    def calculateAnnualMaintenanceCost(self) -> Decimal:
        cost = self._purchasePrice * self.BASE_RATE
        if self._lampHours > self.LAMP_LIMIT_HOURS:
            cost += self.LAMP_SURCHARGE
        return cost

    def __str__(self) -> str:
        return (f"{super().__str__()} | Độ sáng: {self._brightnessLumens} lumen"
                f" | Bóng đèn: {self._lampHours:g} giờ")


# LabRoom (kết tập với Device)
class LabRoom:
    """Phòng thực hành. Chỉ giữ THAM CHIẾU tới thiết bị (không sở hữu)."""

    def __init__(self, roomId: str, roomName: str, capacity: int):
        roomId = _text(roomId, "Mã phòng")
        roomName = _text(roomName, "Tên phòng")
        capacity = _integer(capacity, "Sức chứa", 0, strict_greater=True)
        self._roomId = roomId
        self._roomName = roomName
        self._capacity = capacity
        self._devices: List[Device] = []

    @property
    def roomId(self) -> str:
        return self._roomId

    @property
    def roomName(self) -> str:
        return self._roomName

    @property
    def capacity(self) -> int:
        return self._capacity

    @property
    def devices(self) -> Tuple[Device, ...]:
        return tuple(self._devices)

    def addDevice(self, device: Device) -> None:
        if not isinstance(device, Device):
            raise TypeError("Thiết bị phải là đối tượng Device, không được None")
        if self.findDevice(device.deviceId) is not None:
            raise ValueError(
                f"Phòng {self._roomId} đã có thiết bị mã '{device.deviceId}'")
        self._devices.append(device)

    def removeDevice(self, deviceId: str) -> bool:
        for i, d in enumerate(self._devices):
            if d.deviceId == deviceId:
                del self._devices[i]       # chỉ gỡ tham chiếu, KHÔNG hủy thiết bị
                return True
        return False

    def findDevice(self, deviceId: str) -> Optional[Device]:
        for d in self._devices:
            if d.deviceId == deviceId:
                return d
        return None

    def calculateAnnualMaintenanceCost(self) -> Decimal:
        # Đa hình: chỉ gọi qua kiểu Device, không if/switch theo lớp con
        return sum((d.calculateAnnualMaintenanceCost() for d in self._devices),
                   Decimal(0))

    def getDevicesRequiringMaintenance(self) -> List[Device]:
        return [d for d in self._devices if d.requiresMaintenance()]

    def getNetworkableDevices(self) -> List[INetworkable]:
        """Các thiết bị thực thi INetworkable, không quan tâm lớp cụ thể."""
        return [d for d in self._devices if isinstance(d, INetworkable)]

    def displayDevices(self) -> None:
        print(f"--- Phòng {self._roomId} - {self._roomName} "
              f"(sức chứa {self._capacity}) ---")
        if not self._devices:
            print("  (chưa có thiết bị)")
        for d in self._devices:
            print(f"  {d}")               


class Scanner(Device):
    def calculateAnnualMaintenanceCost(self) -> Decimal:
        return self._purchasePrice * Decimal("0.02")


_ROWS: List[Tuple[int, str, str, str, bool]] = []


def _fmt(value) -> str:
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, (int, float, Decimal)):
        return vnd(value)
    if value is None:
        return "None"
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(str(v) for v in value) + "]"
    return str(value)


def _record(desc: str, expected, actual, passed: bool) -> None:
    _ROWS.append((len(_ROWS) + 1, desc, _fmt(expected), _fmt(actual), passed))


def expect_equal(desc: str, expected, actual) -> None:
    _record(desc, expected, actual, expected == actual)


def expect_raises(desc: str, exc_type, func: Callable, *args) -> None:
    try:
        func(*args)
    except exc_type:
        _record(desc, exc_type.__name__, exc_type.__name__, True)
    except Exception as ex:
        _record(desc, exc_type.__name__, type(ex).__name__, False)
    else:
        _record(desc, exc_type.__name__, "không ném lỗi", False)


def print_table() -> None:
    widths = (4, 46, 24, 24, 7)
    heads = ("STT", "Tình huống", "Kỳ vọng", "Thực tế", "Kết quả")
    line = "+" + "+".join("-" * (w + 2) for w in widths) + "+"

    def row(cells):
        wrapped = [textwrap.wrap(str(c), w) or [""] for c, w in zip(cells, widths)]
        for parts in zip_longest(*wrapped, fillvalue=""):
            print("| " + " | ".join(p.ljust(w) for p, w in zip(parts, widths)) + " |")

    print(line)
    row(heads)
    print(line)
    for no, desc, exp, act, ok in _ROWS:
        row((no, desc, exp, act, "PASS" if ok else "FAIL"))
        print(line)
    passed = sum(1 for r in _ROWS if r[4])
    print(f"TỔNG: {len(_ROWS)} tình huống | PASS: {passed} | "
          f"FAIL: {len(_ROWS) - passed}")


# NHẬP DỮ LIỆU
def build_sample():
    """Hai máy tính, hai máy in, một máy chiếu, hai phòng (đã chia thiết bị)."""
    now = currentYear()
    pc01 = Computer("PC01", "Dell Precision", now - 2, 30_000_000,
                    32, "Intel Core i7", True)                   # có GPU rời
    pc02 = Computer("PC02", "HP ProDesk", now - 7, 15_000_000,
                    8, "Intel Core i5", False)                   # trên 5 năm
    pr01 = Printer("PR01", "Canon LBP", now - 3, 8_000_000,
                   PrinterType.Laser, 120_000, False,            # trên 100.000 trang
                   DeviceStatus.UnderMaintenance)
    pr02 = NetworkPrinter("PR02", "Epson EcoTank", now - 1, 6_000_000,
                          PrinterType.Inkjet, 20_000, True)      # máy in màu, có mạng
    pj01 = Projector("PJ01", "Epson EB-X06", now - 6, 12_000_000,
                     3500, 3_200)                                # đèn trên 3.000 giờ

    roomA = LabRoom("LAB-A", "Phòng thực hành 1", 30)
    roomB = LabRoom("LAB-B", "Phòng thực hành 2", 25)
    for d in (pc01, pc02, pr01):
        roomA.addDevice(d)
    for d in (pr02, pj01):
        roomB.addDevice(d)
    return pc01, pc02, pr01, pr02, pj01, roomA, roomB



# CÁC TRƯỜNG TÌNH HUỐNG KIỂM THỬ
def _pc(age=0, price=10_000_000, gpu=False, did="PC"):
    return Computer(did, "PC", currentYear() - age, price, 16, "i5", gpu)


def _printer(pages=0, color=False, price=10_000_000, did="PR"):
    return Printer(did, "PR", currentYear() - 1, price, PrinterType.Laser,
                   pages, color)


def _projector(lamp=0, price=10_000_000, did="PJ"):
    return Projector(did, "PJ", currentYear() - 1, price, 3000, lamp)


def test_sample_scenario() -> None:
    pc01, pc02, pr01, pr02, pj01, roomA, roomB = build_sample()
    expect_equal("PC01 (GPU rời, 2 năm): 5% + 2% của 30tr", 2_100_000,
                 pc01.calculateAnnualMaintenanceCost())
    expect_equal("PC02 (không GPU, 7 năm): 5% + 1% của 15tr", 900_000,
                 pc02.calculateAnnualMaintenanceCost())
    expect_equal("PR01 (120.000 trang, đen trắng): 4% + 500k", 820_000,
                 pr01.calculateAnnualMaintenanceCost())
    expect_equal("PR02 (20.000 trang, màu): 4% + 300k", 540_000,
                 pr02.calculateAnnualMaintenanceCost())
    expect_equal("PJ01 (đèn 3.200 giờ): 3% + 1,5tr", 1_860_000,
                 pj01.calculateAnnualMaintenanceCost())
    expect_equal("Tổng chi phí phòng A", 3_820_000,
                 roomA.calculateAnnualMaintenanceCost())
    expect_equal("Tổng chi phí phòng B", 2_400_000,
                 roomB.calculateAnnualMaintenanceCost())
    expect_equal("Phòng A cần bảo trì (PC02 quá 5 năm, PR01 đang bảo trì)",
                 ["PC02", "PR01"],
                 [d.deviceId for d in roomA.getDevicesRequiringMaintenance()])
    expect_equal("Phòng B cần bảo trì (PJ01 quá 5 năm)", ["PJ01"],
                 [d.deviceId for d in roomB.getDevicesRequiringMaintenance()])
    expect_raises("Thêm lại CHÍNH thiết bị PC01 vào phòng A", ValueError,
                  roomA.addDevice, pc01)
    other = _pc(did="PC02")
    expect_raises("Thêm đối tượng KHÁC nhưng trùng mã PC02", ValueError,
                  roomA.addDevice, other)
    expect_equal("Sau khi thêm trùng, phòng A vẫn có 3 thiết bị", 3,
                 len(roomA.devices))
    expect_equal("PR01 (máy in thường) không thực thi INetworkable", False,
                 isinstance(pr01, INetworkable))
    expect_equal("PR02 (NetworkPrinter) thực thi INetworkable", True,
                 isinstance(pr02, INetworkable))
    expect_equal("PC01 thực thi INetworkable", True, isinstance(pc01, INetworkable))
    expect_equal("PJ01 không thực thi INetworkable", False,
                 isinstance(pj01, INetworkable))
    expect_equal("Phòng A có 2 thiết bị mạng (PC01, PC02)", 2,
                 len(roomA.getNetworkableDevices()))
    expect_equal("Phòng B có 1 thiết bị mạng (PR02)", 1,
                 len(roomB.getNetworkableDevices()))
    expect_equal("supportsNetwork của PR01 / PR02", [False, True],
                 [pr01.supportsNetwork, pr02.supportsNetwork])


def test_device_validation() -> None:
    now = currentYear()
    expect_raises("Mã thiết bị rỗng", ValueError,
                  Computer, "", "PC", now, 1000, 8, "i5", False)
    expect_raises("Mã thiết bị toàn khoảng trắng", ValueError,
                  Computer, "   ", "PC", now, 1000, 8, "i5", False)
    expect_raises("Tên thiết bị rỗng", ValueError,
                  Computer, "P1", "", now, 1000, 8, "i5", False)
    expect_raises("Giá mua = 0", ValueError,
                  Computer, "P1", "PC", now, 0, 8, "i5", False)
    expect_raises("Giá mua âm", ValueError,
                  Computer, "P1", "PC", now, -1, 8, "i5", False)
    expect_raises("Giá mua NaN", ValueError,
                  Computer, "P1", "PC", now, float("nan"), 8, "i5", False)
    expect_raises("Giá mua là chuỗi", TypeError,
                  Computer, "P1", "PC", now, "abc", 8, "i5", False)
    expect_raises("Năm sử dụng ở tương lai", ValueError,
                  Computer, "P1", "PC", now + 1, 1000, 8, "i5", False)
    expect_raises("Năm sử dụng không phải số nguyên", TypeError,
                  Computer, "P1", "PC", 2020.5, 1000, 8, "i5", False)
    expect_raises("Trạng thái sai kiểu khi tạo", TypeError,
                  Computer, "P1", "PC", now, 1000, 8, "i5", False, "Active")
    expect_equal("Năm = năm hiện tại là hợp lệ (biên): tuổi 0", 0,
                 _pc(age=0).ageInYears)
    pc = _pc()
    expect_raises("Gán lại deviceId (chỉ thiết lập khi khởi tạo)", AttributeError,
                  setattr, pc, "deviceId", "X")
    expect_raises("Gán trạng thái sai kiểu", TypeError, setattr, pc, "status", "Retired")
    pc.status = DeviceStatus.Retired
    expect_equal("Đổi trạng thái hợp lệ sang Retired", DeviceStatus.Retired, pc.status)
    expect_raises("Device là lớp trừu tượng, không tạo trực tiếp", TypeError,
                  Device, "D1", "Ten", now, 1000)
    expect_raises("RAM = 0", ValueError, Computer, "P1", "PC", now, 1000, 0, "i5", False)
    expect_raises("Bộ xử lý rỗng", ValueError,
                  Computer, "P1", "PC", now, 1000, 8, "", False)
    expect_raises("hasDiscreteGpu không phải bool", TypeError,
                  Computer, "P1", "PC", now, 1000, 8, "i5", "yes")
    expect_raises("Số trang đã in âm", ValueError,
                  Printer, "R1", "PR", now, 1000, PrinterType.Laser, -1, False)
    expect_raises("Loại máy in sai kiểu", TypeError,
                  Printer, "R1", "PR", now, 1000, "laser", 0, False)
    expect_raises("Độ sáng = 0", ValueError, Projector, "J1", "PJ", now, 1000, 0, 0)
    expect_raises("Số giờ bóng đèn âm", ValueError,
                  Projector, "J1", "PJ", now, 1000, 3000, -1)


def test_cost_boundaries() -> None:
    expect_equal("Máy tính đúng 5 năm: chưa cộng 1% (5%)", 500_000,
                 _pc(age=5).calculateAnnualMaintenanceCost())
    expect_equal("Máy tính 6 năm: 5% + 1%", 600_000,
                 _pc(age=6).calculateAnnualMaintenanceCost())
    expect_equal("Máy tính có GPU, mới: 5% + 2%", 700_000,
                 _pc(gpu=True).calculateAnnualMaintenanceCost())
    expect_equal("Máy tính có GPU, 6 năm: 5% + 2% + 1%", 800_000,
                 _pc(age=6, gpu=True).calculateAnnualMaintenanceCost())
    expect_equal("Máy in đúng 100.000 trang: chưa cộng 500k", 400_000,
                 _printer(pages=100_000).calculateAnnualMaintenanceCost())
    expect_equal("Máy in 100.001 trang: 4% + 500k", 900_000,
                 _printer(pages=100_001).calculateAnnualMaintenanceCost())
    expect_equal("Máy in màu: 4% + 300k", 700_000,
                 _printer(color=True).calculateAnnualMaintenanceCost())
    expect_equal("Máy in màu và trên 100.000 trang: 4% + 500k + 300k", 1_200_000,
                 _printer(pages=100_001, color=True).calculateAnnualMaintenanceCost())
    expect_equal("Máy chiếu đúng 3.000 giờ: chưa cộng 1,5tr", 300_000,
                 _projector(lamp=3_000).calculateAnnualMaintenanceCost())
    expect_equal("Máy chiếu 3.001 giờ: 3% + 1,5tr", 1_800_000,
                 _projector(lamp=3_001).calculateAnnualMaintenanceCost())
    expect_equal("Giá dạng float 1.000.000,1 không sai số: 5% = 50.000,005",
                 Decimal("50000.005"),
                 _pc(price=1_000_000.1).calculateAnnualMaintenanceCost())

    p = _printer(pages=99_999)
    p.recordPrinting(2)
    expect_equal("recordPrinting(2) vượt ngưỡng 100.000: cộng thêm 500k", 900_000,
                 p.calculateAnnualMaintenanceCost())
    expect_raises("recordPrinting(0)", ValueError, p.recordPrinting, 0)
    j = _projector(lamp=2_999)
    j.addLampHours(2)
    expect_equal("addLampHours vượt 3.000 giờ: cộng thêm 1,5tr", 1_800_000,
                 j.calculateAnnualMaintenanceCost())
    j.replaceLamp()
    expect_equal("replaceLamp: về 0 giờ, hết phụ phí", 300_000,
                 j.calculateAnnualMaintenanceCost())
    expect_raises("addLampHours(âm)", ValueError, j.addLampHours, -1)


def test_status_and_maintenance_filter() -> None:
    d_old_ok = _pc(age=6)
    expect_equal("Thiết bị 6 năm cần bảo trì", True, d_old_ok.requiresMaintenance())
    d_edge = _pc(age=5)
    expect_equal("Thiết bị đúng 5 năm chưa cần bảo trì", False,
                 d_edge.requiresMaintenance())
    d_edge.status = DeviceStatus.UnderMaintenance
    expect_equal("Đang UnderMaintenance thì cần bảo trì", True,
                 d_edge.requiresMaintenance())
    both = _pc(age=7, did="BOTH")
    both.status = DeviceStatus.UnderMaintenance
    room = LabRoom("T", "T", 5)
    room.addDevice(both)
    expect_equal("Vừa cũ vừa đang bảo trì chỉ xuất hiện một lần", 1,
                 len(room.getDevicesRequiringMaintenance()))


def test_networking() -> None:
    pc = _pc()
    expect_equal("Mới tạo: chưa kết nối", False, pc.isConnected)
    expect_equal("Mới tạo: chưa có IP", None, pc.ipAddress)
    pc.connect("192.168.1.10")
    expect_equal("Sau connect: IsConnected = True", True, pc.isConnected)
    expect_equal("Sau connect: có IP", "192.168.1.10", pc.ipAddress)
    expect_raises("Kết nối lại khi đang kết nối", DeviceStateError,
                  pc.connect, "192.168.1.11")
    expect_equal("Kết nối lại bị từ chối: IP cũ được giữ nguyên", "192.168.1.10",
                 pc.ipAddress)
    pc.disconnect()
    expect_equal("Sau disconnect: IsConnected = False", False, pc.isConnected)
    expect_equal("Sau disconnect: không còn IP hoạt động", None, pc.ipAddress)
    pc.disconnect()
    expect_equal("disconnect khi chưa kết nối: không lỗi, vẫn False", False,
                 pc.isConnected)
    pc.connect("10.0.0.5")
    expect_equal("Kết nối lại sau khi ngắt (IP mới)", "10.0.0.5", pc.ipAddress)
    pc.disconnect()

    expect_raises("IP rỗng", ValueError, pc.connect, "")
    expect_raises("IP toàn khoảng trắng", ValueError, pc.connect, "   ")
    expect_raises("IP sai định dạng 999.1.1.1", ValueError, pc.connect, "999.1.1.1")
    expect_raises("IP là chuỗi chữ", ValueError, pc.connect, "abc")
    expect_raises("IP không phải chuỗi", TypeError, pc.connect, 12345)
    expect_equal("Kết nối thất bại thì vẫn chưa kết nối", False, pc.isConnected)

    npr = NetworkPrinter("NP1", "NP", currentYear(), 1000, PrinterType.Laser, 0, False)
    npr.connect("2001:db8::1")
    expect_equal("NetworkPrinter kết nối được (IPv6)", True, npr.isConnected)
    expect_equal("Máy in thường không có connect()", False,
                 hasattr(_printer(), "connect"))
    expect_equal("Máy chiếu không có connect()", False,
                 hasattr(_projector(), "connect"))
    expect_raises("INetworkable là interface, không tạo trực tiếp", TypeError,
                  INetworkable)


def test_lab_room() -> None:
    expect_raises("Mã phòng rỗng", ValueError, LabRoom, "", "Ten", 10)
    expect_raises("Tên phòng rỗng", ValueError, LabRoom, "R", "  ", 10)
    expect_raises("Sức chứa = 0", ValueError, LabRoom, "R", "Ten", 0)
    expect_raises("Sức chứa âm", ValueError, LabRoom, "R", "Ten", -5)
    expect_raises("Sức chứa là số thực", TypeError, LabRoom, "R", "Ten", 10.5)

    room = LabRoom("R1", "Phòng thử", 10)
    expect_equal("Phòng rỗng: tổng chi phí = 0", 0, room.calculateAnnualMaintenanceCost())
    expect_equal("Phòng rỗng: không có thiết bị cần bảo trì", [],
                 room.getDevicesRequiringMaintenance())
    expect_equal("Phòng rỗng: findDevice -> None", None, room.findDevice("X"))
    expect_equal("Phòng rỗng: removeDevice -> False", False, room.removeDevice("X"))

    expect_raises("addDevice(None)", TypeError, room.addDevice, None)
    expect_raises("addDevice(chuỗi)", TypeError, room.addDevice, "PC01")
    pc = _pc(did="PC9")
    room.addDevice(pc)
    expect_equal("findDevice tồn tại", True, room.findDevice("PC9") is pc)
    expect_raises("Danh sách thiết bị chỉ đọc (tuple)", AttributeError,
                  lambda: room.devices.append(pc))
    expect_equal("removeDevice tồn tại -> True", True, room.removeDevice("PC9"))
    expect_equal("Sau khi gỡ, findDevice -> None", None, room.findDevice("PC9"))
    expect_equal("Thiết bị vẫn dùng được sau khi gỡ khỏi phòng", 500_000,
                 pc.calculateAnnualMaintenanceCost())

    tmp = LabRoom("TMP", "Phòng tạm", 5)
    spare = _projector(did="SPARE")
    tmp.addDevice(spare)
    del tmp
    expect_equal("Hủy phòng, thiết bị vẫn tồn tại (kết tập)", 300_000,
                 spare.calculateAnnualMaintenanceCost())

    shared = _pc(did="SHARED")
    r1, r2 = LabRoom("A", "A", 5), LabRoom("B", "B", 5)
    r1.addDevice(shared)
    r2.addDevice(shared)
    r1.removeDevice("SHARED")
    expect_equal("Gỡ khỏi phòng này không ảnh hưởng phòng kia", True,
                 r2.findDevice("SHARED") is shared)

    mixed = LabRoom("M", "Phòng hỗn hợp", 5)
    for d in (_pc(did="A1"), _printer(did="A2"), _projector(did="A3")):
        mixed.addDevice(d)
    manual = sum((d.calculateAnnualMaintenanceCost() for d in mixed.devices),
                 Decimal(0))
    expect_equal("Tổng đa hình = tổng từng thiết bị", manual,
                 mixed.calculateAnnualMaintenanceCost())


def test_extension() -> None:
    room = LabRoom("EXT", "Phòng mở rộng", 5)
    room.addDevice(Scanner("SC01", "Scanner", currentYear(), 5_000_000))
    room.addDevice(_pc(did="PC1"))
    expect_equal("Thêm Scanner (lớp mới) mà không sửa LabRoom: 100k + 500k",
                 600_000, room.calculateAnnualMaintenanceCost())


# Main.py
def main() -> None:
    pc01, pc02, pr01, pr02, pj01, roomA, roomB = build_sample()

    print("\nI. TẠO THIẾT BỊ VÀ THÊM VÀO PHÒNG\n")
    print(f"Phòng {roomA.roomId}: "
          f"{', '.join(d.deviceId for d in roomA.devices)}")
    print(f"Phòng {roomB.roomId}: "
          f"{', '.join(d.deviceId for d in roomB.devices)}")

    print("\nII. THỬ THÊM THIẾT BỊ BỊ TRÙNG MÃ\n")
    for label, dev in (("chính PC01", pc01),
                       ("đối tượng khác mang mã PC02",
                        Computer("PC02", "Máy khác", currentYear(), 10_000_000,
                                 8, "i3", False))):
        try:
            roomA.addDevice(dev)
        except ValueError as ex:
            print(f"  Thêm {label} -> bị từ chối: {ex}")
    print(f"  Số thiết bị phòng A vẫn là {len(roomA.devices)}")

    print("\nIII. DANH SÁCH THIẾT BỊ TRONG TỪNG PHÒNG (đa hình qua __str__)\n")
    roomA.displayDevices()
    roomB.displayDevices()

    print("\nIV. TỔNG CHI PHÍ BẢO TRÌ DỰ KIẾN MỖI NĂM\n")
    for room in (roomA, roomB):
        print(f"  Phòng {room.roomId}: {vnd(room.calculateAnnualMaintenanceCost())}")
        for d in room.devices:
            print(f"      {d.deviceId}: {vnd(d.calculateAnnualMaintenanceCost())}")

    print("\nV. THIẾT BỊ CẦN BẢO TRÌ (UnderMaintenance hoặc dùng trên 5 năm)\n")
    for room in (roomA, roomB):
        found = room.getDevicesRequiringMaintenance()
        print(f"  Phòng {room.roomId}: "
              f"{', '.join(f'{d.deviceId} ({d.status.name}, {d.ageInYears} năm)' for d in found) or '(không có)'}")

    print("\nVI. KẾT NỐI MẠNG CHO CÁC ĐỐI TƯỢNG THỰC THI INetworkable\n")
    networkables: List[INetworkable] = []
    for room in (roomA, roomB):
        networkables.extend(room.getNetworkableDevices())
    for i, n in enumerate(networkables):
        n.connect(f"192.168.1.{10 + i}")      # chỉ dùng chữ ký của INetworkable
        print(f"  {type(n).__name__:<14} -> đã kết nối {n.ipAddress}")

    print("\nVII. DUYỆT THIẾT BỊ MẠNG QUA KIỂU INetworkable\n")
    for n in networkables:
        print(f"  isConnected={n.isConnected}, ip={n.ipAddress}")
    for n in networkables:
        n.disconnect()
    print("  Sau khi disconnect tất cả: "
          + ", ".join(f"({n.isConnected}, {n.ipAddress})" for n in networkables))

    print("\nVIII. KẾT TẬP: VÒNG ĐỜI THIẾT BỊ ĐỘC LẬP VỚI PHÒNG\n")
    spare = Projector("PJ-SPARE", "Máy chiếu dự phòng", currentYear() - 1,
                      9_000_000, 3000, 100)
    print(f"  Tạo {spare.deviceId} khi chưa thuộc phòng nào: "
          f"{vnd(spare.calculateAnnualMaintenanceCost())}/năm")
    roomB.addDevice(spare)
    print(f"  Thêm vào {roomB.roomId}: phòng có {len(roomB.devices)} thiết bị")
    roomB.removeDevice("PJ-SPARE")
    print(f"  Gỡ khỏi phòng: phòng còn {len(roomB.devices)} thiết bị, "
          f"nhưng {spare.deviceId} vẫn tồn tại: {spare.name}")

    print("\nIX. MỞ RỘNG: THÊM LOẠI Scanner MÀ KHÔNG SỬA LabRoom/Device\n")
    ext = LabRoom("LAB-X", "Phòng mở rộng", 10)
    ext.addDevice(Scanner("SC01", "Máy quét", currentYear(), 5_000_000))
    ext.addDevice(pc01)
    print(f"  Tổng chi phí phòng {ext.roomId}: "
          f"{vnd(ext.calculateAnnualMaintenanceCost())}")

    print("\nX. BẢNG TÌNH HUỐNG KIỂM THỬ VÀ KẾT QUẢ CHẠY\n")
    test_sample_scenario()
    test_device_validation()
    test_cost_boundaries()
    test_status_and_maintenance_filter()
    test_networking()
    test_lab_room()
    test_extension()
    print_table()


if __name__ == "__main__":
    main()
