#include <iostream>
#include <chrono>
#include <thread>
//
// Windows basic types 'n' fun
//
#define WIN32_LEAN_AND_MEAN
#include <windows.h>

//
// Optional depending on your use case
//
#include <Xinput.h>

//
// The ViGEm API
//
#include <ViGEm/Client.h>

//
// Link against SetupAPI
//
#pragma comment(lib, "setupapi.lib")

static PVIGEM_CLIENT client;
static PVIGEM_TARGET pad;
static XINPUT_GAMEPAD state = {};

#ifdef __cplusplus
extern "C" {
#endif
  __declspec(dllexport) int connect()
  {
    client = vigem_alloc();

    if (client == nullptr)
    {
      std::cerr << "Uh, not enough memory to do that?!" << std::endl;
      return -1;
    }

    const auto retval = vigem_connect(client);

    if (!VIGEM_SUCCESS(retval))
    {
      std::cerr << "ViGEm Bus connection failed with error code: 0x" << std::hex << retval << std::endl;
      return -1;
    }

    //
    // Allocate handle to identify new pad
    //
    pad = vigem_target_x360_alloc();

    //
    // Add client to the bus, this equals a plug-in event
    //
    const auto pir = vigem_target_add(client, pad);

    //
    // Error handling
    //
    if (!VIGEM_SUCCESS(pir))
    {
      std::cerr << "Target plugin failed with error code: 0x" << std::hex << pir << std::endl;
      return -1;
    }
    
    return 0;
  }
#ifdef __cplusplus
}
#endif

#ifdef __cplusplus
extern "C" {
#endif
  __declspec(dllexport) int set_state(int value)
  {
    //
    // The XINPUT_GAMEPAD structure is identical to the XUSB_REPORT structure
    // so we can simply take it "as-is" and cast it.
    //
    // Call this function on every input state change e.g. in a loop polling
    // another joystick or network device or thermometer or... you get the idea.
    //
      state.wButtons = value;
      vigem_target_x360_update(client, pad, *reinterpret_cast<XUSB_REPORT*>(&state));
      
    return 0;
  }
#ifdef __cplusplus
}
#endif

#ifdef __cplusplus
extern "C" {
#endif
  __declspec(dllexport) int disconnect()
  {
    //
    // We're done with this pad, free resources (this disconnects the virtual device)
    //

    vigem_target_remove(client, pad);
    vigem_target_free(pad);
    vigem_disconnect(client);
    vigem_free(client);
    return 0;
  }
#ifdef __cplusplus
}
#endif