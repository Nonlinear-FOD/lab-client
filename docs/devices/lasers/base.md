# Laser Client Base & Mixins

Common helpers mixed into all laser clients.

- Base: `clients.laser_base_clients.TunableLaserClientBase`
- Mixins:
  - `clients.laser_base_clients.PowerSettable`
  - `clients.laser_base_clients.OSATuningClientMixin`

Most tunable lasers (Ando, Agilent, Photonetics, etc.) inherit these behaviors. If a device page looks sparse, remember its full property/method set also includes the endpoints documented here.

## API Reference

::: clients.laser_base_clients.TunableLaserClientBase
    options:
      show_source: false
      members_order: source
      show_root_heading: true
      heading_level: 2

::: clients.laser_base_clients.PowerSettable
    options:
      show_source: false
      members_order: source
      show_root_heading: true
      heading_level: 2

::: clients.laser_base_clients.OSATuningClientMixin
    options:
      show_source: false
      members_order: source
      show_root_heading: true
      heading_level: 2
