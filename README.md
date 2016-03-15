### Example:

```python
import shouqianba


shouqianba.config.vendor_key = 'd1312asd31123tga123g11'
shouqianba.config.vendor_sn = '138121'

client = shouqianba.ShouqianbaClient()
client.activate("00000008", True)
client.checkin()
client.precreate(1, "1")
```