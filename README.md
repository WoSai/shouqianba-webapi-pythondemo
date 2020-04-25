shouqianba
==========

### Installation:

`pip install https://github.com/WoSai/shouqianba-webapi-pythondemo`

or

`python setup.py install`

### Example:

```python
import shouqianba


shouqianba.config.vendor_key = 'd1312asd31123tga123g11'
shouqianba.config.vendor_sn = '138121'
shouqianba.config.app_id = '2018080800000001'

client = shouqianba.ShouqianbaClient()
client.activate("00000008", True)
client.checkin()
client.precreate(1, "1")
```
