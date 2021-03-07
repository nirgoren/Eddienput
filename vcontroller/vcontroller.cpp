/*
MIT License

Copyright (c) 2021 nirgoren

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
*/
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
#include <ViGEm/Util.h>

//
// Link against SetupAPI
//
#pragma comment(lib, "setupapi.lib")

static bool DINPUT = false;
static PVIGEM_CLIENT client;
static PVIGEM_TARGET pad;
static XINPUT_GAMEPAD state = {};

#ifdef __cplusplus
extern "C" {
#endif
  __declspec(dllexport) int connect(bool use_dinput)
  {
    client = vigem_alloc();

    if (client == nullptr)
    {
      std::cerr << "Failed to allocate client" << std::endl;
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
    DINPUT = use_dinput;
    if (DINPUT)
      pad = vigem_target_ds4_alloc();
    else
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
  __declspec(dllexport) int set_state(int buttons_value, int LT_value, int RT_value)
  {
    //
    // The XINPUT_GAMEPAD structure is identical to the XUSB_REPORT structure
    // so we can simply take it "as-is" and cast it.
    //
      state.wButtons = buttons_value;
      state.bLeftTrigger = LT_value;
      state.bRightTrigger = RT_value;
      if (DINPUT)
      {
        DS4_REPORT rep;
        DS4_REPORT_INIT(&rep);

        // The DualShock 4 expects a different report format, so we call a helper 
        // function which will translate buttons and axes 1:1 from XUSB to DS4
        // format and submit it to the update function afterwards.
        XUSB_TO_DS4_REPORT(reinterpret_cast<PXUSB_REPORT>(&state), &rep);

        vigem_target_ds4_update(client, pad, rep);
      }
      else
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